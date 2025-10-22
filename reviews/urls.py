from django.urls import path
from . import views
from .views import review_landing_page, review_detail_page, add_review

urlpatterns = [
    path('', review_landing_page, name='review_landing'),
    path('<int:schedule_id>/', review_detail_page, name='review_detail'),
    path('<int:schedule_id>/add/', add_review, name='add_review'),
]
