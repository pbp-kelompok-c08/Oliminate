from django.urls import path
from . import views, api_views, proxy_image

app_name = 'scheduling'

urlpatterns = [
    # HTML views
    path('', views.schedule_list, name='schedule_list'),
    path('<int:id>/', views.schedule_detail, name='schedule_detail'),
    path('feed/', views.schedule_feed, name='schedule_feed'),

    # API endpoints (AJAX)
    path('api/list/', api_views.api_list_schedules, name='api_list_schedules'),
    path('api/create/', api_views.api_create_schedule, name='api_create_schedule'),
    path('api/<int:id>/update/', api_views.api_update_schedule, name='api_update_schedule'),
    path('api/<int:id>/delete/', api_views.api_delete_schedule, name='api_delete_schedule'),
    path('api/<int:id>/complete/', api_views.api_mark_completed, name='api_mark_completed'),
    path('api/<int:id>/make-reviewable/', api_views.api_make_reviewable, name='api_make_reviewable'),

    path('proxy-image/', proxy_image, name='proxy_image'),
]
