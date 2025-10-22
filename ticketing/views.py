from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
# 1. Import model & form baru
from .models import Ticket, EventPrice
from .forms import TicketPurchaseForm, EventPriceForm
# 2. Ganti ini ke get_user_model() jika app 'users' sudah jadi
from django.contrib.auth.models import User 
# 3. Import yang kita perlukan
from scheduling.models import Schedule
from django.contrib.auth.decorators import login_required
from django.contrib import messages # Untuk pesan error/sukses

# ==================================
# VIEWS YANG SUDAH ADA (BIARKAN SAJA)
# ==================================
def ticket_list(request):
    # (Logika kamu yang lama di sini)
    tickets = Ticket.objects.all().order_by('-purchase_date')
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
# @login_required 
# (Bisa kamu tambahkan @user_passes_test untuk cek apa dia panitia)
def set_event_price(request):
    """
    View untuk panitia mengatur atau meng-update harga
    untuk sebuah event/schedule.
    """
    if request.method == 'POST':
        form = EventPriceForm(request.POST)
        if form.is_valid():
            schedule = form.cleaned_data['schedule']
            price = form.cleaned_data['price']
            
            # Canggih: Otomatis update jika sudah ada, atau buat baru jika belum
            EventPrice.objects.update_or_create(
                schedule=schedule,
                defaults={'price': price} # Data yang di-set/di-update
            )
            
            messages.success(request, f"Harga untuk {schedule} berhasil diatur/diperbarui!")
            return redirect('set_event_price') # Kembali ke halaman yang sama
    else:
        form = EventPriceForm()

    # Ambil semua harga yang sudah diatur untuk ditampilkan di list
    prices = EventPrice.objects.all().order_by('schedule__date')
    
    return render(request, 'set_price_form.html', { # (Template ini akan kita buat nanti)
        'form': form,
        'prices': prices
    })


# ==================================
# === VIEW LAMA (DIUBAH) UNTUK USER ===
# ==================================
#@login_required # User harus login untuk beli
def buy_ticket(request):
    """
    View untuk user membeli tiket.
    Harga diambil otomatis dari EventPrice.
    """
    if request.method == 'POST':
        form = TicketPurchaseForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            
            # (Pastikan ganti 'User' dengan 'get_user_model()' nanti)
            ticket.buyer = request.user 
            
            # === INI LOGIKA BARUNYA ===
            try:
                # 1. Cari harga di model EventPrice
                event_price_obj = EventPrice.objects.get(schedule=ticket.schedule)
                
                # 2. Copy harga ke tiket
                ticket.price = event_price_obj.price
                
            except EventPrice.DoesNotExist:
                # 3. Jika panitia lupa set harga
                messages.error(request, "Maaf, harga untuk event ini belum diatur oleh panitia. Silakan hubungi organizer.")
                # Tampilkan form-nya lagi dengan pesan error
                return render(request, 'ticket_form.html', {'form': form})
            # ==========================

            ticket.payment_status = 'unpaid'
            ticket.save()
            return redirect('ticket_payment', ticket_id=ticket.id)
    else:
        # Saat user buka halaman (GET request)
        form = TicketPurchaseForm()
        # Filter dropdown agar hanya schedule 'upcoming' yang bisa dibeli
        form.fields['schedule'].queryset = Schedule.objects.filter(status='upcoming')

    return render(request, 'ticket_form.html', {'form': form})

