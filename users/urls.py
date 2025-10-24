from django.urls import path
from users import views
from django.contrib.auth.views import LoginView, LogoutView

app_name = 'users'

urlpatterns = [
    path('register/', views.register_user, name='register'),
    
    path('login/', LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
        next_page='users:main_profile'
    ), name='login'),
    
    path('logout/', LogoutView.as_view(
        next_page='users:login'
    ), name='logout'),
    
    path('profile/', views.main_profile, name='main_profile'),
    
    path('edit/', views.edit_profile, name='edit_profile'),
]