# Jangan lupa [CEK]
from time import localtime
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count

from scheduling.models import Schedule
# from ticketing.models import Ticket
from .models import Review
from .forms import ReviewForm

# Halaman utama review (daftar event yang dapat direview)
def review_landing_page(request):
    events_to_review = Schedule.objects.filter(status='reviewable').annotate(
        avg_rating=Avg('review__rating'),
        review_count=Count('review')
    )
    
    context = {
        'event_list': events_to_review
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
    average_rating = round(average_rating, 1)  # tampil lebih rapi (misal 4.3)

    # can_review = False
    # if request.user.is_authenticated:
    #     can_review = Ticket.objects.filter(
    #         buyer=request.user, 
    #         schedule=schedule
    #     ).exists()
    can_review = request.user.is_authenticated

    # Handle submit review (kalau eligible aja)
    if request.method == 'POST' and can_review:
        form = ReviewForm(request.POST)
        if form.is_valid():
            new_review = form.save(commit=False)
            new_review.reviewer = request.user
            new_review.schedule = schedule
            new_review.save()
            return redirect('review_detail', schedule_id=schedule.id)
    else:
        form = ReviewForm()
    
    context = {
        'schedule': schedule,
        'reviews': reviews,
        'review_form': form,
        'total_reviews': total_reviews,
        'average_rating': average_rating,
        'can_review': can_review,
    }
    return render(request, 'reviews/review_detail_page.html', context)

def add_review(request, schedule_id):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'You must be logged in.'})

        schedule = get_object_or_404(Schedule, pk=schedule_id)
        form = ReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.schedule = schedule
            review.reviewer = request.user
            review.save()

            return JsonResponse({
                'status': 'success',
                'review': {
                    'username': review.reviewer.username,
                    'rating': review.rating,
                    'comment': review.comment,
                    'created_at': localtime(review.created_at).strftime('%b %d, %Y'),
                }
            })

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

def review_page_view(request): # Bikin view baru buat ngetes
    form = ReviewForm()
    
    # Bikin data dummy (kalo error)
    form_errors = False
    
    # Kalo beneran mau ngetes error-nya, uncomment ini
    # if request.method == 'POST':
    #     form = ReviewForm(request.POST)
    #     if not form.is_valid():
    #         form_errors = True
            
    context = {
        'review_form': form,
        'form_errors': form_errors
    }
    # Render template HTML yang kamu buat
    return render(request, 'review_landing_page.html', context)

@login_required
def like_review_view(request, review_id):
    if request.method == 'POST':
        review = get_object_or_404(Review, id=review_id)
        user = request.user
        
        if user in review.likes.all():
            review.likes.remove(user)
        else:
            review.likes.add(user)
        new_like_count = review.likes.count()
        return JsonResponse({'new_count': new_like_count})
    return JsonResponse({'error': 'Invalid request'}, status=400)