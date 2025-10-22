from django.urls import path
from . import views

app_name = 'scheduling'

urlpatterns = [
<<<<<<< HEAD
    path('', views.schedule_list, name='schedule_list'),
    path('<int:id>/', views.schedule_detail, name='schedule_detail'),
    path('feed/', views.schedule_feed, name='schedule_feed'),
    path('create/', views.schedule_create, name='schedule_create'),
    path('<int:id>/edit/', views.schedule_update, name='schedule_update'),
    path('<int:id>/delete/', views.schedule_delete, name='schedule_delete'),
    path('<int:id>/make-reviewable/', views.make_reviewable, name='make_reviewable'),
=======
    #path('', views.home, name='home'),
>>>>>>> origin/feature/users
]

