from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError

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
    title = models.CharField(max_length=2000)
    body = models.TextField()
    tags = models.ManyToManyField('Tag')

    @property
    def liked(self):
        return self.marks.filter(mark_type=POST_MARK_LIKE).count()

    @property
    def disliked(self):
        return self.marks.filter(mark_type=POST_MARK_DISLIKE).count()


class PostMark(models.Model):
    post = models.ForeignKey(Post, related_name='marks')
    mark_type = models.PositiveIntegerField(choices=POST_MARKS)
    user = models.ForeignKey(User, blank=True)


    def save(self, *args, **kwargs):
        if type(self).objects.filter(post=self.post, user=self.user).exists():
            raise ValidationError('Repeated vote is disabled')
        super().save(*args, **kwargs)


class Tag(models.Model):
    title = models.CharField(max_length=500)
    alias = models.CharField(max_length=500)


class Comment(models.Model):
    class Meta:
        ordering = ['-created']

    created = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(Post, related_name='comments')
    user = models.ForeignKey(User, null=True, blank=True, related_name='comments')
    username = models.CharField(max_length=200, blank=True)
    body = models.TextField()