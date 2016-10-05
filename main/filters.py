import django_filters
from rest_framework import filters
from .models import User, Post, Comment

class UserFilter(filters.FilterSet):
    class Meta:
        model = User
        fields = ['id', 'username']


class PostFilter(filters.FilterSet):
    id_gte = django_filters.NumberFilter(name="id", lookup_type='gte')
    body = django_filters.CharFilter(name="body", lookup_type='icontains')
    class Meta:
        model = Post
        fields = ['id_gte', 'tags__alias', 'id', 'body', 'user']


class CommentFilter(filters.FilterSet):
    class Meta:
        model = Comment
        fields = ['post', 'user', 'id']
