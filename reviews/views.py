# Jangan lupa [CEK]
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from scheduling.models import Schedule
from ticketing.models import Ticket
from .models import Review
from .forms import ReviewForm
from django.db.models import Avg

# Halaman utama review (daftar event yang dapat direview)
def review_landing_page(request):
    events_to_review = Schedule.objects.filter(status='reviewable').annotate(
        avg_rating=Avg('reviews__rating')
    )
    
    context = {
        'event_list': events_to_review
    }
    return render(request, 'reviews/review_landing_page.html', context)

# Halaman detail review untuk event tertentu
def review_detail_page(request, schedule_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    reviews = schedule.reviews.all()
    
    can_review = False
    if request.user.is_authenticated:
        can_review = Ticket.objects.filter(
            buyer=request.user, 
            schedule=schedule
        ).exists()

    form = ReviewForm()
    
    context = {
        'schedule': schedule,
        'reviews': reviews,
        'review_form': form,
        'can_review': can_review
    }
    return render(request, 'reviews/review_detail_page.html', context)

@login_required
@require_POST
def add_review_ajax(request, schedule_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    
    can_review = Ticket.objects.filter(
        buyer=request.user, 
        schedule=schedule
    ).exists()
    
    if not can_review:
        # Kirim error sebagai JSON [CEK: ini dia bisa pake toast juga sebenernya]
        return JsonResponse({'status': 'error', 'message': 'Anda tidak diizinkan memberi review.'}, status=403)

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
                'created_at': review.created_at.strftime('%b. %d, %Y')
            }
        })
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)