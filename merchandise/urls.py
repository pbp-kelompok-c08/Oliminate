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
    path('list/', views.merchandise_list_flutter, name='merchandise_list_flutter'),
    path('list/create/', views.merchandise_create_flutter, name='merchandise_create_flutter'),
    path('list/<uuid:id>/edit/', views.merchandise_update_flutter, name='merchandise_update_flutter'),
    path('list/<uuid:id>/delete/', views.merchandise_delete_flutter, name='merchandise_delete_flutter'),
    path('proxy-image/', views.proxy_image, name='proxy_image'),
    path('api/cart/', views.cart_detail_api, name='cart_detail_api'),
    path('api/cart/add/<uuid:merchandise_id>/', views.cart_add_item_api, name='cart_add_item_api'),
    path('api/cart/item/<uuid:item_id>/update/', views.cart_update_item_api, name='cart_update_item_api'),
    path('api/cart/item/<uuid:item_id>/remove/', views.cart_delete_item_api, name='cart_delete_item_api'),
    path('api/cart/checkout/', views.cart_checkout_api, name='cart_checkout_api'),
]
