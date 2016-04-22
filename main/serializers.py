from rest_framework import serializers
from main.models import Post, PostMark, Tag, Comment
from django.contrib.auth.models import User


class PostSerializer(serializers.ModelSerializer):
    rated = serializers.BooleanField(read_only=True)

    class Meta:
        model = Post
        fields = ('id', 'user', 'username', 'title', 'body', 'liked', 'disliked', 'rated', 'created', 'tags')

class PostDetailSerializer(serializers.ModelSerializer):
    rated = serializers.BooleanField(read_only=True)

    class Meta:
        model = Post
        fields = ('id', 'user', 'username', 'title', 'body', 'liked', 'disliked', 'rated', 'created', 'tags', 'comments')



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


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ('id', 'user', 'post', 'body', 'created')