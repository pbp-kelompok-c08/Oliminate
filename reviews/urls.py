from django.urls import path
from .views import review_landing_page, review_detail_page, add_review, edit_review, delete_review

urlpatterns = [
    path('', review_landing_page, name='review_landing'),
    path('<int:schedule_id>/', review_detail_page, name='review_detail'),
    path('<int:schedule_id>/add/', add_review, name='add_review'),
    path('edit/<int:review_id>/', edit_review, name='edit_review'),
    path('delete/<int:review_id>/', delete_review, name='delete_review'),
]
