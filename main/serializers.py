from rest_framework import serializers
from main.models import Post, PostMark, Tag, Comment, UserProfile
from django.contrib.auth.models import User
from djoser import settings as djoser_settings
from djoser import serializers as djoser_serializers
from django.utils.translation import ugettext_lazy as _
from djoser.serializers import UserSerializer


from django.utils import timezone

class DateTimeFielTZ(serializers.DateTimeField):

    def to_representation(self, value):
        value = timezone.localtime(value)
        return super().to_representation(value)


class UsernameMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = kwargs['context']['request'].user

    def validate_username(self, value):
        if self._user.is_authenticated():
            return self._user.username
        elif value:
            value = value.strip()
            if User.objects.filter(username__iexact=value).exists():
                raise serializers.ValidationError(_("This name is used by registered user."))
            return value
        else:
            raise serializers.ValidationError(_("This field cannot be blank."))


class CommentSerializer(UsernameMixin, serializers.ModelSerializer):
    created = DateTimeFielTZ(format="%d.%m.%Y %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'user','username', 'post', 'body', 'created', 'email')


class PostSerializer(UsernameMixin, serializers.ModelSerializer):
    rated = serializers.IntegerField(required=False)
    comments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    created = DateTimeFielTZ(format="%d.%m.%Y %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = Post
        fields = ('id', 'user', 'username', 'body', 'rated', 'created', 'tags', 'comment_count', 'comments', 'email', 'liked_count', 'disliked_count')


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
    #posts = serializers.PrimaryKeyRelatedField(many=True, queryset=Post.objects.all())

    class Meta:
        model = User
        fields = ('id', 'username', 'posts', 'comments')


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

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'vk_id')


#class SocialLoginSerializer(serializers.Serializer):
#    vk_id = serializers.CharField(required=False)


class UserSerializerWithToken(UserSerializer):
    # auth_token = serializers.PrimaryKeyRelatedField(many=True, queryset=Post.objects.all())

    class Meta:
        model = User
        fields = tuple(User.REQUIRED_FIELDS) + (
            User._meta.pk.name,
            User.USERNAME_FIELD,
            'auth_token'
        )
        read_only_fields = (
            User.USERNAME_FIELD,

        )



#djoser_serializers.UserRegistrationSerializer = UserRegistrationSerializer