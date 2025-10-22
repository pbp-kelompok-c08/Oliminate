from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Ticket
from .forms import TicketPurchaseForm
from django.contrib.auth.models import User

# 1️⃣ Daftar semua tiket user (riwayat)
def ticket_list(request):
    tickets = Ticket.objects.all().order_by('-purchase_date')
    return render(request, 'ticket_list.html', {'tickets': tickets})


# 2️⃣ Beli tiket baru
def buy_ticket(request):
    if request.method == 'POST':
        form = TicketPurchaseForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            # kalau nanti sudah ada user model, bisa diganti jadi ticket.buyer = request.user
            ticket.payment_status = 'unpaid'
            ticket.save()
            return redirect('ticket_payment', ticket_id=ticket.id)
    else:
        form = TicketPurchaseForm()
    return render(request, 'ticket_form.html', {'form': form})


# 3️⃣ Konfirmasi pembayaran
def confirm_payment(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.method == 'POST':
        ticket.payment_status = 'paid'
        ticket.save()
        return redirect('ticket_detail', ticket_id=ticket.id)
    return render(request, 'ticket_payment.html', {'ticket': ticket})


# 4️⃣ Lihat detail tiket (misal QR code-nya nanti)
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    return render(request, 'ticket_detail.html', {'ticket': ticket})


# 5️⃣ Simulasi scan tiket di pintu masuk
def scan_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if ticket.payment_status != 'paid':
        message = "Tiket belum dibayar, tidak bisa digunakan!"
    elif ticket.is_used:
        message = "Tiket sudah pernah digunakan!"
    else:
        ticket.is_used = True
        ticket.used_at = timezone.now()
        ticket.save()
        message = "Tiket berhasil divalidasi! Selamat menonton!"
    return render(request, 'ticket_scan.html', {'ticket': ticket, 'message': message})
