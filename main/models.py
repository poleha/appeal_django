from django.db import models
from django.contrib.auth.models import User

POST_MARK_LIKE = 1
POST_MARK_DISLIKE = 2
POST_MARKS = (
    (POST_MARK_LIKE, 'Like'),
    (POST_MARK_DISLIKE, 'Dislike')
)

class Post(models.Model):
    class Meta:
        ordering = ['-created']

    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True, blank=True, related_name='posts')
    username = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    tags = models.ManyToManyField('Tag')
    email = models.EmailField(blank=True, null=True)

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def liked_count(self):
        return self.marks.filter(mark_type=POST_MARK_LIKE).count()

    @property
    def disliked_count(self):
        return self.marks.filter(mark_type=POST_MARK_DISLIKE).count()


class PostMark(models.Model):
    post = models.ForeignKey(Post, related_name='marks')
    mark_type = models.PositiveIntegerField(choices=POST_MARKS)
    user = models.ForeignKey(User, blank=True)

    def save(self, *args, **kwargs):
        type(self).objects.filter(post=self.post, user=self.user).delete()
        if self.user != self.post.user:
            super().save(*args, **kwargs)


class Tag(models.Model):
    class Meta:
        ordering = ('weight', 'title')

    title = models.CharField(max_length=500)
    alias = models.CharField(max_length=500)
    weight = models.IntegerField(default=0, blank=True)


class Comment(models.Model):
    class Meta:
        ordering = ['-created']

    created = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(Post, related_name='comments')
    user = models.ForeignKey(User, null=True, blank=True, related_name='comments')
    username = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    email = models.EmailField(blank=True, null=True)


GOOGLE = 'google'
VK = 'vk'
FACEBOOK = 'facebook'

SOCIAL_NETWORKS = (
    (GOOGLE, 'google'),
    (VK, 'vk'),
    (FACEBOOK, 'facebook'),
)

class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='user_profile')
    external_id = models.CharField(max_length=500, null=True, blank=True)
    network = models.CharField(choices=SOCIAL_NETWORKS, max_length=20)