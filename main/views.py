from main.models import Post, PostMark
from main.serializers import PostSerializer, UserSerializer, PostMarkSerializer
from rest_framework import generics
from django.contrib.auth.models import User
from django.views import generic
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Case, Value, When, BooleanField


class PostList(generics.ListCreateAPIView):
    serializer_class = PostSerializer

    def get_queryset(self):
        queryset = Post.objects.order_by('-created')
        user = self.request.user
        if user.is_authenticated():
            queryset = queryset.annotate(
                rated=Case(
                    When(marks__user=user, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()))
        return queryset

    def perform_create(self, post):
        if self.request.user.is_authenticated():
            user = self.request.user
        else:
            user = None
        post.save(user=user)


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
        if self.request.user.is_authenticated():
            user = self.request.user
        else:
            user = None
        post_mark.save(user=user)


class PostMarkDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = PostMark.objects.all()
    serializer_class = PostMarkSerializer


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

