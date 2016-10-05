from main.models import Post, PostMark, Tag, Comment, UserProfile, POST_MARK_LIKE, POST_MARK_DISLIKE, PostVersion, CommentVersion, SocialAccount
from main.serializers import PostSerializer, UserSerializer, PostMarkSerializer, TagSerializer, CommentSerializer, UserProfileSerializer, SetEmailSerializer
from django.contrib.auth.models import User
from django.db.models import Case, Value, When, IntegerField, Q
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import user_logged_in
from djoser.serializers import TokenSerializer
from rest_framework import filters
import reversion
from django.db import transaction
from rest_framework.pagination import LimitOffsetPagination
from djoser.utils import SendEmailViewMixin
from django.conf import settings
from djoser.views import ActivationView, RegistrationView
from .tokens import UserActivateTokenGenerator
from rest_framework import generics, status, views, exceptions
from rest_framework.serializers import ValidationError
from .permissions import create_permission_for_owner, IsOwnerOnly
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from .filters import UserFilter, PostFilter, CommentFilter


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = PostFilter

    def get_queryset(self):
        queryset = Post.objects.order_by('-history__last_action')
        user = self.request.user
        if user.is_authenticated():
            queryset = queryset.annotate(
                rated=Case(
                    When(Q(marks__user=user, marks__mark_type=POST_MARK_LIKE), then=Value(POST_MARK_LIKE)),
                    When(Q(marks__user=user, marks__mark_type=POST_MARK_DISLIKE), then=Value(POST_MARK_DISLIKE)),
                    default=Value(0),
                    output_field=IntegerField())).exclude(Q(marks__user=user) & Q(rated=0))
        else:
            queryset = queryset.annotate(
                rated=Case(
                    default=Value(0),
                    output_field=IntegerField()))

        queryset = queryset.distinct()
        return queryset

    def save_version(self, serializer):
        post = serializer.instance
        post_version = PostVersion.objects.create(
            post=post,
            user=post.user,
            username=post.username,
            body=post.body,
            email=post.email
        )
        for tag in post.tags.all():
            post_version.tags.add(tag)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        self.save_version(serializer)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        self.save_version(serializer)

    def get_permissions(self):
        if self.action == 'rate':
            return [create_permission_for_owner(allow=False)()]
        else:
            return [create_permission_for_owner(included_methods=('PUT', 'PATCH'))()]

    @detail_route(('PATCH', ))
    def rate(self, request, *args, **kwargs):
        user = request.user
        post = self.get_object()
        if user.is_authenticated() and user == post.user:
            raise exceptions.PermissionDenied(detail='Unable to rate own post')
        user = self.request.user
        mark_type = request.data['rated']
        create = True
        if mark_type:
            existing_marks = PostMark.objects.filter(user=user, post=post)
            if existing_marks.count() > 1:
                existing_marks.delete()
            elif existing_marks.count() == 1:
                existing_mark = existing_marks[0]
                if existing_mark.mark_type == mark_type:
                    existing_mark.delete()
                    create = False
                    post.rated = 0
            if create:
                post_mark, created = PostMark.objects.get_or_create(user=user, post=post,
                                                                    mark_type=mark_type)
                post.rated = mark_type

        serializer = PostSerializer(post)

        return Response(serializer.data)


class ReversionMixin:
    def dispatch(self, *args, **kwargs):
        with transaction.atomic(), reversion.create_revision():
            response = super().dispatch(*args, **kwargs)
            if not self.request.user.is_anonymous():
                reversion.set_user(self.request.user)
            return response


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    filter_class = UserFilter
    filter_backends = (filters.DjangoFilterBackend,)
    serializer_class = UserSerializer


class PoskMarkList(generics.ListCreateAPIView):
    queryset = PostMark.objects.all()
    serializer_class = PostMarkSerializer

    def perform_create(self, post_mark):
        user = self.request.user
        post_mark.save(user=user)


class PostMarkDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = PostMark.objects.all()
    serializer_class = PostMarkSerializer



class UnlimitedPagination(LimitOffsetPagination):
    default_limit = 100
    max_limit = 100


class TagList(generics.ListAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = UnlimitedPagination



class TagDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class CommentViewMixin:
    def save_version(self, serializer):
        comment = serializer.instance
        comment_version = CommentVersion.objects.create(
            comment=comment,
            post=comment.post,
            user=comment.user,
            username=comment.username,
            body=comment.body,
            email=comment.email
        )


    def perform_update(self, serializer):
        super().perform_update(serializer)
        self.save_version(serializer)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        self.save_version(serializer)


class CommentList(CommentViewMixin, ReversionMixin, generics.ListCreateAPIView, SendEmailViewMixin):
    serializer_class = CommentSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = CommentFilter
    queryset = Comment.objects.all()

    subject_template_name = 'comments_email_subject.txt'
    plain_body_template_name = 'comments_email_body.txt'
    html_body_template_name = 'comments_email_body.html'

    def perform_create(self, serializer):
        if self.request.user.is_authenticated():
            user = self.request.user
            serializer.save(user=user, username=user.username)
        else:
            serializer.save()

        comment = serializer.instance

        post_user = comment.post.user
        user_profile = post_user.user_profile
        if user != post_user and user_profile.receive_comments_email:
            self.send_email(**self.get_send_email_kwargs(post_user, comment))

    def get_send_email_kwargs(self, user, comment):
        return {
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            'to_email': user.email,
            'context': self.get_email_context(comment),
        }


    def get_email_context(self, comment):
        domain = settings.DJOSER.get('DOMAIN')
        site_name = settings.DJOSER.get('SITE_NAME')
        return {
            'comment': comment,
            'domain': domain,
            'site_name': site_name,
            'protocol': 'https' if self.request.is_secure() else 'http',
        }


class CommentDetail(CommentViewMixin, ReversionMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer



class AuthorOnlyCommentDetail(CommentDetail):
    permission_classes = (IsOwnerOnly, )


class UserProfileDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserProfileSerializer
    queryset = UserProfile.objects.all()


    def get_object(self):
        user = User.objects.get(**{'pk': self.kwargs['pk']})
        if user.is_authenticated():
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            obj = user_profile
        return obj


class SendActivationEmailView(views.APIView, SendEmailViewMixin):
    subject_template_name = 'activation_email_subject.txt'
    plain_body_template_name = 'activation_email_body.txt'
    token_generator = UserActivateTokenGenerator()

    def get_email_context(self, user):
        context = super().get_email_context(user)
        context['url'] = settings.DJOSER.get('ACTIVATION_URL').format(**context)
        return context

    def post(self, request):
        user = request.user
        if user.is_authenticated:
            user_profile = user.user_profile
            if not user_profile.email_confirmed:
                user = request.user
                if user.is_authenticated:
                    self.send_email(**self.get_send_email_kwargs(user))
        return Response(status=status.HTTP_204_NO_CONTENT)



class SocialLoginMixin:
    def login_user(self, id, network, email, username):
        users_by_id = User.objects.filter(social_accounts__external_id=id, social_accounts__network=network)
        if email:
            users_by_email = User.objects.filter(email=email)
        user = None

        if users_by_id.exists() and email and users_by_email.exists() and users_by_id[0].pk != users_by_email[0].pk:
            raise ValidationError('Пользователь с электронным адресом этой соцсети уже зарегистрирован')
        elif users_by_id.exists():
            user = users_by_id[0]
        elif users_by_email.exists():
            user = users_by_email[0]

        if not user:
            users_by_username = User.objects.filter(username=username)
            k = 0
            while users_by_username.exists():
                k += 1
                username += str(k)
                users_by_username = User.objects.filter(username=username)
            user = User.objects.create(username=username)

        if email and user.email != email:
            user.email = email
            user.save()
            self.send_email(**self.get_send_email_kwargs(user))

        social_account, _ = SocialAccount.objects.get_or_create(user=user)
        social_account.external_id = id
        social_account.network = network
        social_account.save()

        user_profile, _ = UserProfile.objects.get_or_create(user=user)

        token, _ = Token.objects.get_or_create(user=user)
        user_logged_in.send(sender=user.__class__, request=self.request, user=user)
        return Response(
            data=TokenSerializer(token).data,
            status=200,
        )

class SocialLogin(SendActivationEmailView, SocialLoginMixin):

    def post(self, request):
        id = request.data['id']
        username = request.data['username']
        network = request.data['network']
        email = request.data.get('email', None)
        return self.login_user(id, network, email, username)


class VkLogin(SendActivationEmailView, SocialLoginMixin):

    def post(self, request):
        import requests
        from .vk_key import APP_SECRET
        code = request.data['code']
        network = 'vk'
        redirect_url = request.data['redirect_url']
        url = "https://oauth.vk.com/access_token?client_id=5414620&client_secret={}&redirect_uri={}&code={}".format(APP_SECRET, redirect_url, code)
        r = requests.post(url)
        if r.status_code == 200:
            json1 = r.json()
            user_id = json1['user_id']
            #token = json['access_token']
            email = json1['email']
            url = 'https://api.vk.com/method/users.get?user_ids={}&v=5.53'.format(user_id)
            r = requests.post(url)
            if r.status_code == 200:
                json2 = r.json()
                user_info = json2['response'][0]
                username = "{} {}".format(user_info['first_name'], user_info['last_name'])
                return self.login_user(user_id, network, email, username)


class ActivationViewWithToken(ActivationView):
    token_generator = UserActivateTokenGenerator()

    def action(self, serializer):
        serializer.user.user_profile.email_confirmed = True
        serializer.user.user_profile.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegistrationViewWithToken(RegistrationView):
    token_generator = UserActivateTokenGenerator()


class SetEmail(SendActivationEmailView):
    serializer_class = SetEmailSerializer

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.serializer_class(data=request.data, instance=user)
        if serializer.is_valid():
            user.email = serializer.validated_data['email']
            user.save()
            self.send_email(**self.get_send_email_kwargs(user))
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST

            )

