from django.conf.urls import url, include
from main import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'posts', views.PostViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'post_marks', views.PostMarkViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^user_profile/(?P<pk>[0-9]+)/$', views.UserProfileDetail.as_view()),
    url(r'^auth/social_login/$', views.SocialLogin.as_view()),
    url(r'^auth/vk_login/$', views.VkLogin.as_view()),
    url(r'^auth/activate/$', views.ActivationViewWithToken.as_view()),
    url(r'^auth/register/$', views.RegistrationViewWithToken.as_view()),
    url(r'^send_user_activation_email/$', views.SendActivationEmailView.as_view()),
    url(r'^auth/set_email/(?P<pk>[0-9]+)/$', views.SetEmail.as_view()),
]