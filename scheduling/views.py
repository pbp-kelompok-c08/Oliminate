from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Schedule

def schedule_list(request):
    """
    Render halaman utama daftar jadwal.
    Halaman ini akan memakai AJAX untuk memuat data, tapi kita tetap bisa
    kirimkan 'schedules' sebagai fallback jika perlu.
    """
    schedules = Schedule.objects.exclude(status='reviewable').order_by('date', 'time')
    return render(request, 'scheduling/schedule_list.html', {
        'schedules': schedules,
        'user': request.user,  # agar template bisa akses request.user.role
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
