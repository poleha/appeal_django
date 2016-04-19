from django.db import models
from django.contrib.auth.models import User

# Create your models here.

POST_MARK_LIKE = 1
POST_MARK_DISLIKE = 2
POST_MARKS = (
    (POST_MARK_LIKE, 'Like'),
    (POST_MARK_DISLIKE, 'Dislike')
)

class Post(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True, blank=True, related_name='posts')
    username = models.CharField(max_length=200)
    title = models.CharField(max_length=2000)
    body = models.TextField()

    @property
    def liked(self):
        return self.marks.filter(mark_type=POST_MARK_LIKE).count()

    @property
    def disliked(self):
        return self.marks.filter(mark_type=POST_MARK_DISLIKE).count()

    @property
    def rated(self):
        return False

class PostMark(models.Model):
    post = models.ForeignKey(Post, related_name='marks')
    mark_type = models.PositiveIntegerField(choices=POST_MARKS)
    user = models.ForeignKey(User, null=True, blank=True)
    ip = models.CharField(max_length=15, blank=True, null=True)
    session_key = models.CharField(max_length=2000, blank=True, null=True)