from main.models import Post, PostMark, Tag
from main.serializers import PostSerializer, UserSerializer, PostMarkSerializer, TagSerializer
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
        fields = ['id_gte', 'tags__alias']


class PostList(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = PostFilter

    def get_queryset(self):
        queryset = Post.objects.order_by('-created')
        user = self.request.user
        if user.is_authenticated():
            queryset = queryset.annotate(
                rated=Case(
                    When(Q(marks__user=user) | Q(user=user), then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField())).distinct()
        else:
            queryset = queryset.annotate(
                rated=Case(
                    default=Value(True),
                    output_field=BooleanField()))
        return queryset

    def perform_create(self, post):
        if self.request.user.is_authenticated():
            user = self.request.user
            post.save(user=user, username=user.username)
        else:
            post.save()




class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
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


"""
class LoginView(generic.View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            print(token.key)
            return JsonResponse({'user_id': user.pk, 'username': user.username, 'token_key': token.key})
"""
