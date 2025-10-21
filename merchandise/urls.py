from django.urls import path
from . import views

app_name = 'merchandise'

urlpatterns = [
    path('', views.merchandise_list, name='merchandise_list'),
    path('<uuid:id>/', views.merchandise_detail, name='merchandise_detail'),
    path('create', views.merchandise_create, name='merchandise_create'),
    path('<uuid:id>/edit/', views.merchandise_update, name='merchandise_update'),
    path('<uuid:id>/delete/', views.merchandise_delete, name='merchandise_delete'),
]
