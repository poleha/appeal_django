from main.models import Post, PostMark, Tag, Comment, UserProfile, POST_MARK_LIKE, POST_MARK_DISLIKE
from main.serializers import PostSerializer, UserSerializer, PostMarkSerializer, TagSerializer, CommentSerializer, UserProfileSerializer
from rest_framework import generics
from django.contrib.auth.models import User
from django.db.models import Case, Value, When, IntegerField, Q
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import user_logged_in
from djoser.serializers import TokenSerializer

import django_filters
from rest_framework import filters


class PostFilter(filters.FilterSet):
    id_gte = django_filters.NumberFilter(name="id", lookup_type='gte')
    #tags_alias = django_filters.CharFilter(name="id", lookup_type='gte')
    class Meta:
        model = Post
        fields = ['id_gte', 'tags__alias', 'id']



class PostViewMixin:
    def get_queryset(self):
        queryset = Post.objects.order_by('-created')
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


        return queryset


class PostList(PostViewMixin, generics.ListCreateAPIView):
    serializer_class = PostSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = PostFilter

    def perform_create(self, post):
        if self.request.user.is_authenticated():
            user = self.request.user
            post.save(user=user, username=user.username)
        else:
            post.save()


class PostDetail(PostViewMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer


class UserList(generics.ListAPIView):
    queryset = User.objects.all()
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



class TagList(generics.ListAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class TagDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class CommentFilter(filters.FilterSet):
    class Meta:
        model = Comment
        fields = ['post']

class CommentList(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = CommentFilter
    queryset = Comment.objects.all()

    def perform_create(self, comment):
        if self.request.user.is_authenticated():
            user = self.request.user
            comment.save(user=user, username=user.username)
        else:
            comment.save()

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

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated():
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            instance = user_profile
            serializer = self.get_serializer(instance)
            return Response(serializer.data)



class SocialLogin(generics.GenericAPIView):

    def post(self, request):
        id = request.data['id']
        username = request.data['username']
        network = request.data['network']
        users_by_id = User.objects.filter(user_profile__external_id=id, user_profile__network=network)
        if users_by_id.exists():
            user = users_by_id[0]
        else:
            users_by_username = User.objects.filter(username=username)
            k = 0
            while users_by_username.exists():
                k += 1
                username += str(k)
                users_by_username = User.objects.filter(username=username)
            user = User.objects.create(username=username)

        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        user_profile.external_id = id
        user_profile.network = network
        user_profile.save()

        token, _ = Token.objects.get_or_create(user=user)
        user_logged_in.send(sender=user.__class__, request=self.request, user=user)
        return Response(
            data=TokenSerializer(token).data,
            status=200,
        )





                #class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
#    queryset = Tag.objects.all()
#    serializer_class = TagSerializer