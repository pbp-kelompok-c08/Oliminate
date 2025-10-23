from django.urls import path
from . import views

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('buy/', views.buy_ticket, name='buy_ticket'),
    path('<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('<int:ticket_id>/payment/', views.confirm_payment, name='ticket_payment'),
    path('<int:ticket_id>/scan/', views.scan_ticket, name='ticket_scan'),
    path('set-price/', views.set_event_price, name='set_event_price'),
    path('get-price/<int:schedule_id>/', views.get_price, name='get_price'),
    path('generate_qr/<int:ticket_id>/', views.generate_qr, name='generate_qr'),
    #path('tickets/json/', views.ticket_list_json, name='ticket_list_json'),
    path('json/', views.ticket_list_json, name='ticket_list_json'),
    path('pay/<int:ticket_id>/', views.pay_ticket, name='pay_ticket'),  # <<-- endpoint AJAX yang baru
]
