from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'users' 

urlpatterns = [
    path('', views.main_profile, name='users_root'),
    path('main-profile/', views.main_profile, name='main_profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('register/', views.register_user, name='register_user'),
    path('login/', views.login_user, name='login'),
]

