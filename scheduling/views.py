from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from .models import Schedule

def schedule_list(request):
    # 🕒 Step 1: auto-mark as completed jika waktu sudah lewat
    now = timezone.now()
    for s in Schedule.objects.filter(status='upcoming'):
        schedule_time = timezone.make_aware(
            timezone.datetime.combine(s.date, s.time)
        )
        if schedule_time < now:
            s.status = 'completed'
            s.save(update_fields=['status'])

    # 🧩 Step 2: semua user (termasuk non-login) bisa lihat jadwal
    schedules = Schedule.objects.exclude(status='reviewable').order_by('date', 'time')

    # Default filter: "Semua"
    filter_type = 'all'

    # Kalau user login & pilih filter "mine"
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