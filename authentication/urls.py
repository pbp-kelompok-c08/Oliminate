from django.urls import path

from . import views

app_name = 'authentication'

urlpatterns = [
    path('api/csrf/', views.csrf_token_view, name='csrf'),
    path('api/login/', views.login_view, name='login'),
    path('api/register/', views.register_view, name='register'),
    path('api/logout/', views.logout_view, name='logout'),
    path('api/session/', views.session_view, name='session'),
    path('api/profile/update/', views.profile_update_view, name='profile_update'),
]
