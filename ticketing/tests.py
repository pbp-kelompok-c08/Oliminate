# ticketing/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import Ticket, EventPrice
from users.models import User
from scheduling.models import Schedule
import json

class TicketingTestCase(TestCase):

    def setUp(self):
        # Buat user biasa dan organizer
        self.user = User.objects.create_user(username='user1', password='pass123', role='user')
        self.organizer = User.objects.create_user(username='org1', password='pass123', role='organizer')

        # Buat schedule
        self.schedule = Schedule.objects.create(name="Match 1", date=timezone.now(), status='upcoming')

        # Buat harga event
        self.event_price = EventPrice.objects.create(schedule=self.schedule, price=50000)

        # Buat tiket
        self.ticket = Ticket.objects.create(
            schedule=self.schedule,
            buyer=self.user,
            price=self.event_price.price,
            payment_status='unpaid'
        )

        self.client = Client()

    # ===== FORM TEST =====
    def test_ticket_purchase_form_valid(self):
        self.client.login(username='user1', password='pass123')
        response = self.client.post(reverse('buy_ticket'), {
            'schedule': self.schedule.id,
            'payment_method': 'ewallet'
        })
        self.assertEqual(response.status_code, 302)  # Redirect ke payment
        ticket = Ticket.objects.last()
        self.assertEqual(ticket.buyer, self.user)
        self.assertEqual(ticket.price, self.event_price.price)

    def test_event_price_form_valid(self):
        self.client.login(username='org1', password='pass123')
        response = self.client.post(reverse('set_event_price'), {
            'schedule': self.schedule.id,
            'price': 75000
        })
        self.assertEqual(response.status_code, 302)
        self.event_price.refresh_from_db()
        self.assertEqual(float(self.event_price.price), 75000.0)

    # ===== VIEW TEST =====
    def test_get_price_json(self):
        self.client.login(username='user1', password='pass123')
        url = reverse('get_price', args=[self.schedule.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(data['price'], 50000.0)

    def test_ticket_list_view_authenticated(self):
        self.client.login(username='user1', password='pass123')
        response = self.client.get(reverse('ticket_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ticket #")

    def test_ticket_list_view_organizer_redirect(self):
        self.client.login(username='org1', password='pass123')
        response = self.client.get(reverse('ticket_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('set_event_price'), response.url)

    def test_pay_ticket_ajax(self):
        self.client.login(username='user1', password='pass123')
        url = reverse('pay_ticket', args=[self.ticket.id])
        response = self.client.post(url)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.payment_status, 'paid')

    def test_generate_qr(self):
        self.client.login(username='user1', password='pass123')
        url = reverse('generate_qr', args=[self.ticket.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertIn('qr_code', data)
        self.assertTrue(len(data['qr_code']) > 0)

    def test_scan_ticket(self):
        self.ticket.payment_status = 'paid'
        self.ticket.save()
        self.client.login(username='user1', password='pass123')
        url = reverse('ticket_scan', args=[self.ticket.id])
        response = self.client.get(url)
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.is_used)
        self.assertIn("Tiket berhasil divalidasi", response.content.decode())

    def test_ticket_list_json_ajax(self):
        self.client.login(username='user1', password='pass123')
        url = reverse('ticket_list_json')
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertIn('<tr>', data['html'])

    def test_set_event_price_ajax_view(self):
        self.client.login(username='org1', password='pass123')
        url = reverse('set_event_price_ajax')
        response = self.client.post(url, {
            'schedule_id': self.schedule.id,
            'price': 90000
        })
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.event_price.refresh_from_db()
        self.assertEqual(float(self.event_price.price), 90000.0)
        self.assertIn('<tr>', data['html'])
