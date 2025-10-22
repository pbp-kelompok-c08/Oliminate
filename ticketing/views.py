from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Ticket, EventPrice
from .forms import TicketPurchaseForm, EventPriceForm
from users.models import User 
from scheduling.models import Schedule
from django.contrib import messages

# ==================================
# === VIEW TICKET_LIST (DIPERBAIKI) ===
# ==================================
def ticket_list(request):
    """
    Menampilkan daftar tiket milik user yang login.
    Sekarang dengan tambahan filter berdasarkan status.
    """
    
    # 1. Ambil parameter 'status' dari URL. 
    #    Default-nya None (artinya 'semua')
    filter_status = request.GET.get('status', None)

    try:
        user_id = request.session['user_id']
        buyer = User.objects.get(id=user_id)
        
        # 2. Siapkan query dasar (semua tiket milik user ini)
        base_query = Ticket.objects.filter(buyer=buyer)

        # 3. Terapkan filter JIKA ada
        if filter_status == 'paid':
            tickets_query = base_query.filter(payment_status='paid')
        elif filter_status == 'unpaid':
            tickets_query = base_query.filter(payment_status='unpaid')
        else:
            # Jika filter_status=None atau 'semua', ambil semua
            tickets_query = base_query
        
        # 4. Terapkan ordering di akhir
        tickets = tickets_query.order_by('-purchase_date')

    except (KeyError, User.DoesNotExist):
        tickets = Ticket.objects.none() 
        if not filter_status: # Hanya tampilkan pesan jika user belum filter
            messages.info(request, "Silakan login untuk melihat riwayat tiket Anda.")

    # 5. Kirim 'tickets' DAN 'active_filter' ke template
    return render(request, 'ticket_list.html', {
        'tickets': tickets,
        'active_filter': filter_status # Ini untuk highlight tombol
    })

# ... (sisa view-mu: confirm_payment, ticket_detail, dll... biarkan saja) ...
def confirm_payment(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.method == 'POST':
        ticket.payment_status = 'paid'
        ticket.save()
        return redirect('ticket_detail', ticket_id=ticket.id)
    return render(request, 'ticket_payment.html', {'ticket': ticket})

def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    return render(request, 'ticket_detail.html', {'ticket': ticket})

def scan_ticket(request, ticket_id):
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

def set_event_price(request):
    try:
        user_id = request.session['user_id']
        user = User.objects.get(id=user_id)
        if user.role != 'organizer':
            messages.error(request, "Anda tidak punya hak akses ke halaman ini.")
            return redirect('users:main_profile')
    except (KeyError, User.DoesNotExist):
        messages.error(request, "Anda harus login sebagai panitia untuk mengakses halaman ini.")
        return redirect('users:login')

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

def buy_ticket(request):
    try:
        user_id = request.session['user_id']
        buyer = User.objects.get(id=user_id)
        if buyer.role != 'user':
            messages.error(request, "Hanya user yang dapat membeli tiket. Akun panitia tidak bisa.")
            return redirect('users:main_profile')
    except (KeyError, User.DoesNotExist):
        messages.error(request, "Anda harus login untuk membeli tiket.")
        return redirect('users:login')

    if request.method == 'POST':
        form = TicketPurchaseForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.buyer = buyer 
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

