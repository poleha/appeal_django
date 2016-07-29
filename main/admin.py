from django.contrib import admin
from reversion.admin import VersionAdmin
from . import models

# Register your models here.

@admin.register(models.Post)
class PostAdmin(VersionAdmin):
    pass


@admin.register(models.Comment)
class CommentAdmin(VersionAdmin):
    pass



@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(models.PostHistory)
class PostHistoryAdmin(admin.ModelAdmin):
    pass
