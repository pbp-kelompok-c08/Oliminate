from django.urls import path
from . import views

app_name = 'merchandise'

urlpatterns = [
    path('', views.merchandise_list, name='merchandise_list'),
    path('<uuid:id>/', views.merchandise_detail, name='merchandise_detail'),
    path('create', views.merchandise_create, name='merchandise_create'),
    path('<uuid:id>/edit/', views.merchandise_update, name='merchandise_update'),
    path('<uuid:id>/delete/', views.merchandise_delete, name='merchandise_delete'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<uuid:merchandise_id>/', views.cart_add_item, name='cart_add_item'),
    path('cart/item/<uuid:item_id>/update/', views.cart_update_item, name='cart_update_item'),
    path('cart/item/<uuid:item_id>/remove/', views.cart_remove_item, name='cart_remove_item'),
    path('cart/checkout/', views.cart_checkout, name='cart_checkout'),
    path('cart/pay/', views.cart_pay, name='cart_pay'),
]
