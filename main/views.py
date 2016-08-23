from main.models import Post, PostMark, Tag, Comment, UserProfile, POST_MARK_LIKE, POST_MARK_DISLIKE, PostVersion, CommentVersion, SocialAccount
from main.serializers import PostSerializer, UserSerializer, PostMarkSerializer, TagSerializer, CommentSerializer, UserProfileSerializer
from django.contrib.auth.models import User
from django.db.models import Case, Value, When, IntegerField, Q
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import user_logged_in
from djoser.serializers import TokenSerializer
import django_filters
from rest_framework import filters
import reversion
from django.db import transaction
from rest_framework.pagination import LimitOffsetPagination
from djoser.utils import SendEmailViewMixin
from django.conf import settings
from djoser.views import ActivationView, RegistrationView
from .tokens import UserActivateTokenGenerator
from rest_framework import generics, status, views
from rest_framework.serializers import ValidationError


class ReversionMixin:
    def dispatch(self, *args, **kwargs):
        with transaction.atomic(), reversion.create_revision():
            response = super().dispatch(*args, **kwargs)
            if not self.request.user.is_anonymous():
                reversion.set_user(self.request.user)
            return response



class PostFilter(filters.FilterSet):
    id_gte = django_filters.NumberFilter(name="id", lookup_type='gte')
    body = django_filters.CharFilter(name="body", lookup_type='icontains')
    class Meta:
        model = Post
        fields = ['id_gte', 'tags__alias', 'id', 'body', 'user']


class PostViewMixin:
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
        super().perform_create(serializer)
        self.save_version(serializer)


class PostList(PostViewMixin, ReversionMixin, generics.ListCreateAPIView):
    serializer_class = PostSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = PostFilter

    def perform_create(self, post):
        if self.request.user.is_authenticated():
            user = self.request.user
            post.save(user=user, username=user.username)
        else:
            post.save()


class AuthorOnlyPermission:
    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.pk

class AuthorOnlyMixin(generics.GenericAPIView):
    def get_permissions(self):
        permissions = super().get_permissions()
        permissions.append(AuthorOnlyPermission())
        return permissions


class PostDetail(PostViewMixin, ReversionMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer



class AuthorOnlyPostDetail(AuthorOnlyMixin, PostDetail):
    pass



class UserFilter(filters.FilterSet):
    #id_gte = django_filters.NumberFilter(name="id", lookup_type='gte')
    #body = django_filters.CharFilter(name="body", lookup_type='icontains')
    #tags_alias = django_filters.CharFilter(name="id", lookup_type='gte')
    class Meta:
        model = User
        fields = ['id', 'username']

class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    filter_class = UserFilter
    filter_backends = (filters.DjangoFilterBackend,)
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
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


class CommentFilter(filters.FilterSet):
    class Meta:
        model = Comment
        fields = ['post', 'user', 'id']

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



class AuthorOnlyCommentDetail(AuthorOnlyMixin, CommentDetail):
    pass


class RatePostView(PostViewMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer

    def perform_update(self, post):
        user = self.request.user
        if user and user.is_authenticated():
            mark_type = post._validated_data['rated']
            create = True
            if mark_type:
                existing_marks = PostMark.objects.filter(user=user, post=post.instance)
                if existing_marks.count() > 1:
                    existing_marks.delete()
                elif existing_marks.count() == 1:
                    existing_mark = existing_marks[0]
                    if existing_mark.mark_type == mark_type:
                        existing_mark.delete()
                        create = False
                        post.instance.rated = 0
                if create:
                    post_mark, created = PostMark.objects.get_or_create(user=user, post=post.instance,
                                                                        mark_type=mark_type)
                    post.instance.rated = mark_type


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


class SocialLogin(SendActivationEmailView):

    def post(self, request):
        id = request.data['id']
        username = request.data['username']
        network = request.data['network']
        email = request.data.get('email', None)
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

        social_account, _ = SocialAccount.objects.get_or_create(user=user)
        social_account.external_id = id
        social_account.network = network
        social_account.save()

        user_profile, _ = UserProfile.objects.get_or_create(user=user)

        if user.email and not user_profile.email_confirmed:
            self.send_email(**self.get_send_email_kwargs(user))

        token, _ = Token.objects.get_or_create(user=user)
        user_logged_in.send(sender=user.__class__, request=self.request, user=user)
        return Response(
            data=TokenSerializer(token).data,
            status=200,
        )

class ActivationViewWithToken(ActivationView):
    token_generator = UserActivateTokenGenerator()

    def action(self, serializer):
        serializer.user.user_profile.email_confirmed = True
        serializer.user.user_profile.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class RegistrationViewWithToken(RegistrationView):
    token_generator = UserActivateTokenGenerator()




