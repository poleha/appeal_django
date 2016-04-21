from rest_framework import serializers
from main.models import Post, PostMark, Tag
from django.contrib.auth.models import User


class PostSerializer(serializers.ModelSerializer):
    rated = serializers.BooleanField(read_only=True)


    class Meta:
        model = Post
        fields = ('id', 'user', 'username', 'title', 'body', 'liked', 'disliked', 'rated', 'created', 'tags')

    #username = serializers.ReadOnlyField(source='user.username')

class UserSerializer(serializers.ModelSerializer):
    posts = serializers.PrimaryKeyRelatedField(many=True, queryset=Post.objects.all())

    class Meta:
        model = User
        fields = ('id', 'username', 'posts')


class PostMarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMark
        fields = ('id', 'post', 'mark_type', 'user')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'title', 'alias')
