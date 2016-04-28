from main.models import Post, PostMark, Tag, Comment, POST_MARK_LIKE, POST_MARK_DISLIKE
from main.serializers import PostSerializer, UserSerializer, PostMarkSerializer, TagSerializer, CommentSerializer
from rest_framework import generics
from django.contrib.auth.models import User
from django.db.models import Case, Value, When, BooleanField, Q


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
                liked=Case(
                    When(Q(marks__user=user, marks__mark_type=POST_MARK_LIKE), then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField())).distinct()

            queryset = queryset.annotate(
                disliked=Case(
                    When(Q(marks__user=user, marks__mark_type=POST_MARK_DISLIKE), then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField())).distinct()

            queryset = queryset.annotate(
                rated=Case(
                    When(Q(marks__user=user), then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField())).distinct()
        else:
            queryset = queryset.annotate(
                rated=Case(
                    default=Value(False),
                    output_field=BooleanField()))
            queryset = queryset.annotate(
                liked=Case(
                    default=Value(False),
                    output_field=BooleanField()))
            queryset = queryset.annotate(
                disliked=Case(
                    default=Value(False),
                    output_field=BooleanField()))


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


#class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
#    queryset = Tag.objects.all()
#    serializer_class = TagSerializer