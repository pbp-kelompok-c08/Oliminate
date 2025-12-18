import json
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count

from scheduling.models import Schedule
from ticketing.models import Ticket
from .models import Review
from .forms import ReviewForm

# Halaman utama review (daftar event yang dapat direview)
def review_landing_page(request):

    sort_by = request.GET.get('sort', '-review_count') 
    
    valid_sort_options = {
        'highest_rating': '-avg_rating', 
        'lowest_rating': 'avg_rating',   
        'most_reviewed': '-review_count',
    }
    
    order_by_field = valid_sort_options.get(sort_by, '-review_count')

    events_to_review = Schedule.objects.filter(status='reviewable').annotate(
        avg_rating=Avg('review__rating'),
        review_count=Count('review')
    ).order_by(order_by_field)

    for event in events_to_review:
        avg = event.avg_rating or 0
        full_stars = int(avg)  # jumlah bintang penuh
        half_stars = 1 if (avg - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_stars
        event.full_stars = range(full_stars)
        event.half_star = half_stars
        event.empty_stars = range(empty_stars)
    
    context = {
        'event_list': events_to_review,
        'current_sort': sort_by,
    }
    return render(request, 'review_landing_page.html', context)

# Halaman detail review untuk event tertentu
def review_detail_page(request, schedule_id):
    # Ambil jadwal/event terkait
    schedule = get_object_or_404(Schedule, id=schedule_id)
    reviews = Review.objects.filter(schedule=schedule).select_related('reviewer')

    # Hitung total dan rata-rata rating
    total_reviews = reviews.count()
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    average_rating = round(average_rating, 1)
    full_stars = int(average_rating)  # jumlah bintang penuh
    half_star = (average_rating - full_stars) >= 0.5  # True kalau ada setengah
    empty_stars = 5 - full_stars - (1 if half_star else 0)

    can_review = False

    if request.user.is_authenticated:
        can_review = Ticket.objects.filter(
            buyer=request.user, 
            schedule=schedule
        ).exists()

    # if request.method == 'POST' and can_review:
    #     form = ReviewForm(request.POST)
    #     if form.is_valid():
    #         new_review = form.save(commit=False)
    #         new_review.reviewer = request.user
    #         new_review.schedule = schedule
    #         new_review.save()
    #         return redirect('review_detail', schedule_id=schedule.id)
    # else:
    #     form = ReviewForm()
    
    context = {
        'schedule': schedule,
        'reviews': reviews,
        # 'review_form': form,
        'total_reviews': total_reviews,
        'average_rating': average_rating,
        'full_stars': range(full_stars),
        'half_star': half_star,
        'empty_stars': range(empty_stars),
        'can_review': can_review,
    }
    return render(request, 'review_detail.html', context)

@login_required
def add_review(request, schedule_id):
    # Ambil schedule yang mau direview
    schedule = get_object_or_404(Schedule, id=schedule_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    can_review = Ticket.objects.filter(
            buyer=request.user, 
            schedule=schedule
        ).exists()
    
    if not can_review:
        message = "Anda tidak memenuhi syarat untuk menambahkan review pertandingan ini (diperlukan tiket)."
        if is_ajax:
            return JsonResponse({'success': False, 'message': message}, status=403)
        else:
            return redirect('review_detail', schedule_id=schedule_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.schedule = schedule     
            review.reviewer = request.user  
            review.save()
            if is_ajax:
                return JsonResponse({'success': True, 'message': 'Review berhasil ditambahkan!'})
            else:
                return redirect('review_detail', schedule_id=schedule.id)
        else:
            context = {'review_form': form, 'schedule': schedule}
            if is_ajax:
                return render(request, 'review_form_fragment.html', context, status=400)
            else:
                return render(request, 'review_form.html', context)
    else:
        form = ReviewForm()
        context = {
            'schedule': schedule,
            'review_form': form,
            'title': 'Tambah Review',
            'form_action_url': reverse('add_review', args=[schedule.id])
        }
        template_name = "review_form.html"
        if is_ajax:
            template_name = "review_form_fragment.html"
        return render(request, template_name, context)

@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    schedule = review.schedule 
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if review.reviewer != request.user:
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'Anda tidak memiliki izin untuk mengedit review ini.'}, status=403)
        else:
            return HttpResponseForbidden("Anda tidak memiliki izin untuk mengedit review ini.")

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            if is_ajax:
                return JsonResponse({'success': True, 'message': 'Review berhasil diperbarui!'})
            else:
                return redirect('review_detail', schedule_id=schedule.id)
    else:
        form = ReviewForm(instance=review)

    context = {
        'review_form': form,
        'schedule': schedule,
        'review': review,
        'title': 'Edit Review',
        'form_action_url': reverse('edit_review', args=[review.id])
    }
    template_name = "review_edit.html"  
    if is_ajax:
        template_name = "review_form_fragment.html"

    return render(request, template_name, context) 

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    schedule = review.schedule
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if review.reviewer != request.user:
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'Anda tidak memiliki izin untuk menghapus review ini.'}, status=403)
        else:
            return HttpResponseForbidden("Anda tidak memiliki izin untuk menghapus review ini.")
        
    if request.method == 'POST':
        reviewer_name = review.reviewer.username
        review.delete()
        if is_ajax:
            return JsonResponse({
                'success': True, 
                'message': f"Review berhasil dihapus.",
            })
        else:
            return redirect('review_detail', schedule_id=schedule.id)
    context = {
        'review': review,
        'schedule': schedule
    }
    return render(request, 'review_confirm_delete.html', context)

def get_review_landing_json(request):
    sort_by = request.GET.get('sort', '-review_count') 
    valid_sort_options = {
        'highest_rating': '-avg_rating', 
        'lowest_rating': 'avg_rating',   
        'most_reviewed': '-review_count',
    }
    order_by_field = valid_sort_options.get(sort_by, '-review_count')

    events = Schedule.objects.filter(status='reviewable').annotate(
        avg_rating=Avg('review__rating'),
        review_count=Count('review')
    ).order_by(order_by_field)

    data = []
    for event in events:
        data.append({
            "id": event.id,
            "team1": event.team1,
            "team2": event.team2,
            "category": event.category,
            "location": event.location,
            "date": str(event.date),
            "time": str(event.time),
            "image_url": event.image_url,
            "avg_rating": event.avg_rating or 0.0,
            "review_count": event.review_count,
        })
    return JsonResponse(data, safe=False)

def get_review_detail_json(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    reviews = Review.objects.filter(schedule=schedule).select_related('reviewer').order_by('-created_at')
    
    can_review = False
    if request.user.is_authenticated:
        can_review = Ticket.objects.filter(buyer=request.user, schedule=schedule).exists()
    
    reviews_data = []
    for r in reviews:
        pfp_url = None
        if r.reviewer.profile_picture:
            pfp_url = request.build_absolute_uri(r.reviewer.profile_picture.url)
        
        is_edited = False
        if r.updated_at and r.created_at:
             # Beri toleransi 1 detik agar tidak dianggap edit saat baru dibuat
            is_edited = (r.updated_at - r.created_at).total_seconds() > 1
            
        reviews_data.append({
            "id": r.id,
            "reviewer": r.reviewer.username,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.strftime("%d %B %Y"),
            "is_owner": request.user == r.reviewer,
            "profile_picture": pfp_url,
            "is_edited": is_edited,
        })

    return JsonResponse({
        "schedule": {
            "team1": schedule.team1,
            "team2": schedule.team2,
            "category": schedule.category,
            "location": schedule.location,
            "date": str(schedule.date), # Convert ke string
            "time": str(schedule.time),
        },
        "can_review": can_review,
        "reviews": reviews_data
    })

@csrf_exempt
def add_review_flutter(request, schedule_id):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({"status": "error", "message": "Belum login"}, status=403)
        
        try:
            # --- UBAH BAGIAN INI (Gunakan request.POST) ---
            # data = json.loads(request.body) 
            data = request.POST 
            
            schedule = get_object_or_404(Schedule, id=schedule_id)

            if Review.objects.filter(schedule=schedule, reviewer=request.user).exists():
                return JsonResponse({"status": "error", "message": "Anda sudah mereview event ini!"}, status=400)

            if not Ticket.objects.filter(buyer=request.user, schedule=schedule).exists():
                 return JsonResponse({"status": "error", "message": "Anda tidak memiliki tiket"}, status=403)

            review = Review.objects.create(
                schedule=schedule,
                reviewer=request.user,
                rating=int(data['rating']),
                comment=data['comment']
            )
            return JsonResponse({"status": "success", "message": "Review berhasil ditambahkan!"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error"}, status=405)

@csrf_exempt
def edit_review_flutter(request, review_id):
    if request.method == 'POST':
        try:
            # --- UBAH BAGIAN INI JUGA ---
            data = request.POST
            
            review = Review.objects.get(id=review_id)
            if review.reviewer != request.user:
                return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)
            
            review.rating = int(data['rating'])
            review.comment = data['comment']
            review.save()
            return JsonResponse({"status": "success", "message": "Review berhasil diubah!"}, status=200)
        except Review.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Review tidak ditemukan"}, status=404)
    return JsonResponse({"status": "error"}, status=405)

@csrf_exempt
def delete_review_flutter(request, review_id):
    if request.method == 'POST':
        try:
            review = Review.objects.get(id=review_id)
            if review.reviewer != request.user:
                return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)
            review.delete()
            return JsonResponse({"status": "success"}, status=200)
        except Review.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Not found"}, status=404)
    return JsonResponse({"status": "error"}, status=405)