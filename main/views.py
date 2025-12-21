from django.shortcuts import render
from scheduling.models import Schedule
from django.http import JsonResponse

def homepage(request):
    # Ambil 5 jadwal terdekat (status 'upcoming')
    schedules = Schedule.objects.filter(status='upcoming').order_by('date', 'time')[:10]
    return render(request, 'main/homepage.html', {'schedules': schedules})

def get_schedules_json(request):
    # Filter only upcoming schedules and sort by date/time (nearest first)
    schedules = Schedule.objects.filter(status='upcoming').order_by('date', 'time')[:10].values(
        'team1', 'team2', 'category', 'date', 'time', 'location', 'image_url'
    )
    return JsonResponse(list(schedules), safe=False)
