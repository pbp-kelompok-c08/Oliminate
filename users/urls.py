from django.urls import path
from . import views

app_name = 'users'  # supaya bisa pakai {% url 'users:...' %}

urlpatterns = [
    path('main-profile/', views.main_profile, name='main_profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
]

