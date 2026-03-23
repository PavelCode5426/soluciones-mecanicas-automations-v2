from django.urls import path

from facebook import views

app_name = 'facebook'

urlpatterns = [
    path(r'facebook-posts', views.FacebookPostListAPIView.as_view()),
]
