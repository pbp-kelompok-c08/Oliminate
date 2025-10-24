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

    events_to_review = Schedule.objects.filter(status='reviewable').annotate(
        avg_rating=Avg('review__rating'),
        review_count=Count('review')
    )

    for event in events_to_review:
        avg = event.avg_rating or 0
        full_stars = int(avg)  # jumlah bintang penuh
        half_stars = 1 if (avg - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_stars
        event.full_stars = range(full_stars)
        event.half_star = half_stars
        event.empty_stars = range(empty_stars)
    
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
        message = "You are not eligible to review this event (ticket required)."
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
                return JsonResponse({'success': True, 'message': 'Review added successfully!'})
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
            'title': 'Add Review', # <-- 1. Hilangkan tanda komentar ini
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
            return JsonResponse({'success': False, 'message': 'You are not authorized to edit this review.'}, status=403)
        else:
            return HttpResponseForbidden("You are not authorized to edit this review.")
        
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            if is_ajax:
                return JsonResponse({'success': True, 'message': 'Review updated successfully!'})
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
            return JsonResponse({'success': False, 'message': 'You are not authorized to delete this review.'}, status=403)
        else:
            return HttpResponseForbidden("You are not authorized to delete this review.")
        
    if request.method == 'POST':
        reviewer_name = review.reviewer.username
        review.delete()
        if is_ajax:
            return JsonResponse({
                'success': True, 
                'message': f"Review from {reviewer_name} has been deleted."
            })
        else:
            return redirect('review_detail', schedule_id=schedule.id)
    context = {
        'review': review,
        'schedule': schedule
    }
    return render(request, 'review_confirm_delete.html', context)