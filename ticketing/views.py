from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Ticket, EventPrice
from .forms import TicketPurchaseForm, EventPriceForm
from users.models import User
from scheduling.models import Schedule
# HAPUS 'login_required' bawaan Django
# from django.contrib.auth.decorators import login_required 
from django.contrib import messages

# ==================================
# VIEWS YANG SUDAH ADA (BIARKAN SAJA)
# ==================================

# Kita akan ubah ticket_list sedikit
def ticket_list(request):
    # --- LOGIKA AMBIL USER DARI SESSION ---
    try:
        user_id = request.session['user_id']
        buyer = User.objects.get(id=user_id)
        # Filter tiket HANYA untuk user yang login
        tickets = Ticket.objects.filter(buyer=buyer).order_by('-purchase_date')
    except (KeyError, User.DoesNotExist):
        # Jika tidak login, tampilkan daftar kosong atau paksa login
        messages.error(request, "Silakan login untuk melihat riwayat tiket.")
        return redirect('users:login') # Redirect ke login temanmu
    # --- SELESAI ---

    return render(request, 'ticket_list.html', {'tickets': tickets})

def confirm_payment(request, ticket_id):
    # (Logika kamu yang lama di sini)
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.method == 'POST':
        ticket.payment_status = 'paid'
        ticket.save()
        return redirect('ticket_detail', ticket_id=ticket.id)
    return render(request, 'ticket_payment.html', {'ticket': ticket})

def ticket_detail(request, ticket_id):
    # (Logika kamu yang lama di sini)
    ticket = get_object_or_404(Ticket, id=ticket_id)
    return render(request, 'ticket_detail.html', {'ticket': ticket})

def scan_ticket(request, ticket_id):
    # (Logika kamu yang lama di sini)
    ticket = get_object_or_404(Ticket, id=ticket_id)
    message = ""
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

# ==================================
# === VIEW BARU UNTUK PANITIA ===
# ==================================
def set_event_price(request):
    # (Logika kamu yang lama di sini, sudah benar)
    if request.method == 'POST':
        form = EventPriceForm(request.POST)
        if form.is_valid():
            schedule = form.cleaned_data['schedule']
            price = form.cleaned_data['price']
            EventPrice.objects.update_or_create(
                schedule=schedule,
                defaults={'price': price}
            )
            messages.success(request, f"Harga untuk {schedule} berhasil diatur/diperbarui!")
            return redirect('set_event_price')
    else:
        form = EventPriceForm()
    prices = EventPrice.objects.all().order_by('schedule__date')
    return render(request, 'set_price_form.html', {
        'form': form,
        'prices': prices
    })


# ==================================
# === VIEW USER (INI YANG DIUBAH) ===
# ==================================
def buy_ticket(request):
    """
    View untuk user membeli tiket.
    """
    # --- LOGIKA AMBIL USER DARI SESSION ---
    try:
        user_id = request.session['user_id']
        buyer = User.objects.get(id=user_id) 
    except (KeyError, User.DoesNotExist):
        # Jika tidak ada di session, paksa login
        messages.error(request, "Anda harus login untuk membeli tiket.")
        return redirect('users:login') # Redirect ke login temanmu
    # --- SELESAI ---
    
    if request.method == 'POST':
        form = TicketPurchaseForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            
            # === INI PERBAIKANNYA ===
            # Gunakan 'buyer' yang kita ambil dari session
            ticket.buyer = buyer
            # ==========================
            
            try:
                event_price_obj = EventPrice.objects.get(schedule=ticket.schedule)
                ticket.price = event_price_obj.price
            except EventPrice.DoesNotExist:
                messages.error(request, "Maaf, harga untuk event ini belum diatur oleh panitia.")
                return render(request, 'ticket_form.html', {'form': form})

            ticket.payment_status = 'unpaid'
            ticket.save()
            return redirect('ticket_payment', ticket_id=ticket.id)
    else:
        form = TicketPurchaseForm()
        form.fields['schedule'].queryset = Schedule.objects.filter(status='upcoming')

    return render(request, 'ticket_form.html', {'form': form})

