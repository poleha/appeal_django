from rest_framework import serializers
from main.models import Post, PostMark, Tag, Comment
from django.contrib.auth.models import User
from djoser import settings as djoser_settings
from djoser import serializers as djoser_serializers
from django.utils.translation import ugettext_lazy as _


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ('id', 'user','username', 'post', 'body', 'created')



class PostSerializer(serializers.ModelSerializer):
    rated = serializers.BooleanField(read_only=True)
    comments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    def __new__(cls, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']
            user = kwargs['context']['request'].user
            if user.is_authenticated():
                data['username'] = user.username
        return super().__new__(cls, *args, **kwargs)

    class Meta:
        model = Post
        fields = ('id', 'user', 'username', 'body', 'liked', 'disliked', 'rated', 'created', 'tags', 'comment_count', 'comments')


"""
class PostDetailSerializer(serializers.ModelSerializer):
    rated = serializers.BooleanField(read_only=True)
    #comments = serializers.HyperlinkedRelatedField(many=True, view_name='comment-detail', read_only=True)
    #comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ('id', 'user', 'username', 'body', 'liked', 'disliked', 'rated', 'created', 'tags', 'comments')
"""


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


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(style={'input_type': 'password'},
                                     write_only=True,
                                     validators=djoser_settings.get('PASSWORD_VALIDATORS'))

    password2 = serializers.CharField(style={'input_type': 'password'},
                                     write_only=True,
                                     validators=djoser_settings.get('PASSWORD_VALIDATORS'))

    email = serializers.EmailField(required=True)


    def validate_email(self, value):
        value = value.strip()
        exists = User.objects.filter(email=value).exists()
        if exists:
            raise serializers.ValidationError(_("This email already in use."))
        return value



    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']

    def validate(self, data):
        password2 = data.pop('password2')
        if data['password'] != password2:
            raise serializers.ValidationError(_("Passwords not equal."))


        return data

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        if djoser_settings.get('SEND_ACTIVATION_EMAIL'):
            user.is_active = False
            user.save(update_fields=['is_active'])
        return user

#TODO monkey patch but settings don't work
djoser_serializers.UserRegistrationSerializer = UserRegistrationSerializer