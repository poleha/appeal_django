from django.conf.urls import url
from main import views

urlpatterns = [
    url(r'^posts/$', views.PostList.as_view()),
    url(r'^posts/(?P<pk>[0-9]+)/$', views.PostDetail.as_view()),
    url(r'^users/$', views.UserList.as_view()),
    url(r'^users/(?P<pk>[0-9]+)/$', views.UserDetail.as_view()),
    url(r'^post_marks/$', views.PoskMarkList.as_view()),
    url(r'^post_marks/(?P<pk>[0-9]+)/$', views.PostMarkDetail.as_view()),
    url(r'^tags/$', views.TagList.as_view()),
    url(r'^tags/(?P<pk>[0-9]+)/$', views.TagDetail.as_view()),
    url(r'^comments/$', views.CommentList.as_view()),
    #url(r'^comments/(?P<pk>[0-9]+)/$', views.CommentDetail.as_view(), name='comment-detail'),
#    url(r'^ajax_login/$', views.LoginView.as_view()),
]