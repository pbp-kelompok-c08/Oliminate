from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Ticket, EventPrice
from .forms import TicketPurchaseForm, EventPriceForm
from users.models import User 
from scheduling.models import Schedule
from django.contrib import messages
from django.http import JsonResponse
import qrcode, base64
from io import BytesIO
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

def get_user_from_session(request):
    try:
        user_id = request.session['user_id']
        user = User.objects.get(id=user_id)
        return user
    except (KeyError, User.DoesNotExist):
        return None
    
def get_price(request, schedule_id):
    try:
        event_price = EventPrice.objects.get(schedule__id=schedule_id)
        price = float(event_price.price)
    except EventPrice.DoesNotExist:
        price = 0.0
    return JsonResponse({'price': price})

def ticket_list(request):
    """
    Menampilkan daftar tiket milik user yang login.
    Sekarang dengan tambahan filter berdasarkan status.
    """

    filter_status = request.GET.get('status', None)

    # GUNAKAN CARA INI:
    if request.user.is_authenticated:
        buyer = request.user # Langsung ambil user yang login

        if request.user.role == 'organizer':
            # Jika dia organizer, lempar ke halaman atur harga
            return redirect('set_event_price')

        base_query = Ticket.objects.filter(buyer=buyer)

        if filter_status == 'paid':
            tickets_query = base_query.filter(payment_status='paid')
        elif filter_status == 'unpaid':
            tickets_query = base_query.filter(payment_status='unpaid')
        else:
            tickets_query = base_query

        tickets = tickets_query.order_by('-purchase_date')

    else: # Ini pengganti blok 'except'
        tickets = Ticket.objects.none() 
        if not filter_status:
            messages.info(request, "Silakan login untuk melihat riwayat tiket Anda.")

    return render(request, 'ticket_list.html', {
        'tickets': tickets,
        'active_filter': filter_status 
    })

def generate_qr(request, ticket_id):
    ticket = Ticket.objects.get(id=ticket_id)
    data = f"TIKET-{ticket.id}-{ticket.buyer.username}"
    
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return JsonResponse({'qr_code': img_str})

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

@login_required(login_url='users:login') # Otomatis cek login & redirect
def set_event_price(request):
    
    # Langsung cek role dari request.user
    if request.user.role != 'organizer':
        messages.error(request, "Anda tidak punya hak akses ke halaman ini.")
        return redirect('users:main_profile') 

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

@login_required(login_url='users:login') # Otomatis cek login
def buy_ticket(request):
    
    # Langsung ambil user dan cek role
    buyer = request.user
    if buyer.role != 'user':
        messages.error(request, "Hanya user yang dapat membeli tiket. Akun panitia tidak bisa.")
        return redirect('users:main_profile')

    if request.method == 'POST':
        form = TicketPurchaseForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.buyer = buyer # Langsung set buyer
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

def ticket_list_json(request):
    """
    View AJAX GET untuk mengambil daftar tiket dalam bentuk HTML partial (tabel body).
    """
    filter_status = request.GET.get('status')

    # Ganti pengecekan session dengan request.user
    if request.user.is_authenticated and request.user.role == 'user':
        buyer = request.user
        base_query = Ticket.objects.filter(buyer=buyer)

        if filter_status == 'paid':
            tickets_query = base_query.filter(payment_status='paid')
        elif filter_status == 'unpaid':
            tickets_query = base_query.filter(payment_status='unpaid')
        else:
            tickets_query = base_query

        tickets = tickets_query.order_by('-purchase_date')
    else:
        tickets = Ticket.objects.none()

    # render partial HTML
    html = render_to_string('partials/ticket_table_body.html', {'tickets': tickets})
    return JsonResponse({'html': html})

@require_POST
def pay_ticket(request, ticket_id):
    # optional: cek apakah request.headers.get('x-requested-with') == 'XMLHttpRequest'
    ticket = get_object_or_404(Ticket, id=ticket_id)
    # pastikan only owner dapat mengubah? (opsional)
    try:
        ticket.payment_status = 'paid'
        ticket.save()
        return JsonResponse({'success': True, 'ticket_id': ticket.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
@csrf_exempt
@login_required(login_url='users:login')
def set_event_price_ajax(request):
    """
    Handle AJAX request untuk menambah/mengupdate harga event tanpa reload halaman.
    """
    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        price = request.POST.get('price')

        if not schedule_id or not price:
            return JsonResponse({'success': False, 'error': 'Data tidak lengkap.'})

        try:
            schedule = Schedule.objects.get(id=schedule_id)
            obj, created = EventPrice.objects.update_or_create(
                schedule=schedule,
                defaults={'price': price}
            )
            # render ulang partial daftar harga
            prices = EventPrice.objects.all().order_by('schedule__date')
            html = render_to_string('partials/event_price_list.html', {'prices': prices})
            return JsonResponse({'success': True, 'html': html})
        except Schedule.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Schedule tidak ditemukan.'})
    return JsonResponse({'success': False, 'error': 'Metode tidak valid.'})


# ============================================
# FLUTTER API ENDPOINTS
# ============================================

@csrf_exempt
def schedules_json_flutter(request):
    """
    GET /ticketing/schedules/json/
    Returns all schedules with their prices for Flutter app.
    """
    schedules = Schedule.objects.all().order_by('date', 'time')
    
    result = []
    for s in schedules:
        # Get price if exists
        try:
            event_price = EventPrice.objects.get(schedule=s)
            price = float(event_price.price)
        except EventPrice.DoesNotExist:
            price = None
        
        result.append({
            'id': s.id,
            'category': s.category,
            'team1': s.team1,
            'team2': s.team2,
            'location': s.location,
            'date': s.date.strftime('%Y-%m-%d'),
            'time': s.time.strftime('%H:%M:%S'),
            'status': s.status,
            'image_url': s.image_url or '',
            'caption': s.caption or '',
            'price': price,
        })
    
    return JsonResponse({'schedules': result})


@csrf_exempt
def tickets_flutter(request):
    """
    GET /ticketing/tickets-flutter/?username=xxx&ticket_id=xxx
    Returns tickets for a specific user or a specific ticket.
    """
    username = request.GET.get('username')
    ticket_id = request.GET.get('ticket_id')
    
    if ticket_id:
        # Get specific ticket
        try:
            ticket = Ticket.objects.get(id=ticket_id)
            schedule = ticket.schedule
            tickets_data = [{
                'id': str(ticket.id),
                'event_name': f"{schedule.category.upper()}: {schedule.team1} vs {schedule.team2}",
                'schedule': str(schedule),
                'price': float(ticket.price),
                'status': ticket.payment_status,
                'is_used': ticket.is_used,
                'buyer_username': ticket.buyer.username if ticket.buyer else '',
                'category': schedule.category,
                'date': schedule.date.strftime('%Y-%m-%d'),
                'time': schedule.time.strftime('%H:%M:%S'),
                'location': schedule.location,
                'schedule_image': schedule.image_url or '',
            }]
            return JsonResponse({'status': 'success', 'tickets': tickets_data})
        except Ticket.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Ticket not found', 'tickets': []})
    
    if not username:
        return JsonResponse({'status': 'error', 'message': 'Username required', 'tickets': []})
    
    try:
        user = User.objects.get(username=username)
        tickets = Ticket.objects.filter(buyer=user).order_by('-purchase_date')
        
        tickets_data = []
        for t in tickets:
            schedule = t.schedule
            tickets_data.append({
                'id': str(t.id),
                'event_name': f"{schedule.category.upper()}: {schedule.team1} vs {schedule.team2}",
                'schedule': str(schedule),
                'price': float(t.price),
                'status': t.payment_status,
                'is_used': t.is_used,
                'buyer_username': t.buyer.username if t.buyer else '',
                'category': schedule.category,
                'date': schedule.date.strftime('%Y-%m-%d'),
                'time': schedule.time.strftime('%H:%M:%S'),
                'location': schedule.location,
                'schedule_image': schedule.image_url or '',
            })
        
        return JsonResponse({'status': 'success', 'tickets': tickets_data})
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found', 'tickets': []})


@csrf_exempt
def buy_flutter(request):
    """
    POST /ticketing/buy-flutter/
    Body JSON: {schedule_id, payment_method, username}
    Creates a new ticket for Flutter app.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        schedule_id = data.get('schedule_id')
        payment_method = data.get('payment_method', 'ewallet')
        username = data.get('username')
        
        if not schedule_id or not username:
            return JsonResponse({'status': 'error', 'message': 'schedule_id and username required'})
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'})
        
        try:
            schedule = Schedule.objects.get(id=schedule_id)
        except Schedule.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Schedule not found'})
        
        # Get price
        try:
            event_price = EventPrice.objects.get(schedule=schedule)
            price = event_price.price
        except EventPrice.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Harga belum diatur untuk event ini'})
        
        # Create ticket
        ticket = Ticket.objects.create(
            buyer=user,
            schedule=schedule,
            price=price,
            payment_status='unpaid',
            payment_method=payment_method,
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Tiket berhasil dibuat',
            'ticket_id': ticket.id,
        })
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
def pay_flutter(request, ticket_id):
    """
    POST /ticketing/pay-flutter/<ticket_id>/
    Confirms payment for Flutter app.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        ticket.payment_status = 'paid'
        ticket.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Pembayaran berhasil dikonfirmasi',
            'ticket_id': ticket.id,
        })
    except Ticket.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Ticket not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
def scan_flutter(request, ticket_id):
    """
    GET /ticketing/scan-flutter/<ticket_id>/
    Validates/scans a ticket for Flutter app.
    """
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        
        if ticket.payment_status != 'paid':
            return JsonResponse({
                'status': 'error',
                'message': 'Tiket belum dibayar, tidak bisa digunakan!',
            })
        
        if ticket.is_used:
            return JsonResponse({
                'status': 'error',
                'message': 'Tiket sudah pernah digunakan!',
            })
        
        ticket.is_used = True
        ticket.used_at = timezone.now()
        ticket.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Tiket berhasil divalidasi! Selamat menonton!',
        })
    except Ticket.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Ticket not found'}, status=404)


@csrf_exempt
def set_price_flutter(request):
    """
    POST /ticketing/set-price-flutter/
    Body JSON: {schedule_id, price, username}
    Sets price for a schedule (organizer only) for Flutter app.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        schedule_id = data.get('schedule_id')
        price = data.get('price')
        username = data.get('username')
        
        if not schedule_id or price is None:
            return JsonResponse({'status': 'error', 'message': 'schedule_id and price required'})
        
        # Check if user is organizer
        if username:
            try:
                user = User.objects.get(username=username)
                if user.role != 'organizer':
                    return JsonResponse({'status': 'error', 'message': 'Hanya organizer yang dapat mengatur harga'})
            except User.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'User not found'})
        
        try:
            schedule = Schedule.objects.get(id=schedule_id)
        except Schedule.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Schedule not found'})
        
        # Update or create price
        EventPrice.objects.update_or_create(
            schedule=schedule,
            defaults={'price': price}
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'Harga untuk {schedule} berhasil diatur',
        })
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})