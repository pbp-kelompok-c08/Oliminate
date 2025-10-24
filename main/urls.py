from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('get-schedules-json/', views.get_schedules_json, name='get_schedules_json'),
]
