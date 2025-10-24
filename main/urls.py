from django.urls import path
from . import views

urlpatterns = [
<<<<<<< HEAD
    path('main_page/', views.main_page, name='main_page'),
    #path('', views.home, name='home'),
=======
    path('', views.homepage, name='homepage'),
    path('get-schedules-json/', views.get_schedules_json, name='get_schedules_json'),
>>>>>>> origin/main
]
