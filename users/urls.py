from django.urls import path, include
from . import views

urlpatterns = [
    path('edit-profile/', views.edit_profile, name='edit_profile'),
]
