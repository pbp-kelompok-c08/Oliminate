from django.urls import path
from .views import (
    review_landing_page, 
    review_detail_page, 
    add_review, 
    edit_review, 
    delete_review,
    get_review_landing_json,
    get_review_detail_json,
    add_review_flutter,
    edit_review_flutter,
    delete_review_flutter,
)

urlpatterns = [
    path('', review_landing_page, name='review_landing'),
    path('<int:schedule_id>/', review_detail_page, name='review_detail'),
    path('<int:schedule_id>/add/', add_review, name='add_review'),
    path('edit/<int:review_id>/', edit_review, name='edit_review'),
    path('delete/<int:review_id>/', delete_review, name='delete_review'),
    path('json/', get_review_landing_json, name='json_landing'),
    path('json/<int:schedule_id>/', get_review_detail_json, name='json_detail'),
    path('add-flutter/<int:schedule_id>/', add_review_flutter, name='add_flutter'),
    path('edit-flutter/<int:review_id>/', edit_review_flutter, name='edit_flutter'),
    path('delete-flutter/<int:review_id>/', delete_review_flutter, name='delete_flutter'),
]