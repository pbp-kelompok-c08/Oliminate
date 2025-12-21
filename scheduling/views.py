from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Schedule
import requests

def schedule_list(request):
    # Semua user (termasuk non-login) bisa lihat jadwal
    schedules = Schedule.objects.exclude(status='reviewable').order_by('date', 'time')

    # Default filter: "Semua"
    filter_type = 'all'

    # Kalau user login & milih filter jadwal saya
    if request.user.is_authenticated and request.GET.get('filter') == 'mine':
        schedules = schedules.filter(organizer=request.user)
        filter_type = 'mine'

    return render(request, 'scheduling/schedule_list.html', {
        'schedules': schedules,
        'filter_type': filter_type,
        'user': request.user,
    })


def schedule_detail(request, id):
    schedule = get_object_or_404(Schedule, pk=id)
    return render(request, 'scheduling/schedule_detail.html', {'schedule': schedule})

def schedule_feed(request):
    """
    JSON sederhana (mis. untuk FullCalendar). Ini bukan endpoint CRUD AJAX.
    """
    schedules = Schedule.objects.all()
    data = [
        {
            "title": f"{s.category}: {s.team1} vs {s.team2}",
            "start": f"{s.date}T{s.time}",  # format ISO
            "url": f"/scheduling/{s.id}/"
        }
        for s in schedules
    ]
    return JsonResponse(data, safe=False)

def proxy_image(request):
    image_url = request.GET.get('url')
    if not image_url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        # Fetch image from external source
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Return the image with proper content type
        return HttpResponse(
            response.content,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except requests.RequestException as e:
        return HttpResponse(f'Error fetching image: {str(e)}', status=500)