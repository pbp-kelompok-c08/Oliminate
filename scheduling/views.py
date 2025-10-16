from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Schedule
from .forms import ScheduleForm
from django.shortcuts import redirect


# 1️⃣ Daftar semua jadwal
def schedule_list(request):
    schedules = Schedule.objects.all().order_by('date', 'time')
    return render(request, 'scheduling/schedule_list.html', {'schedules': schedules})

# 2️⃣ Detail satu pertandingan
def schedule_detail(request, id):
    schedule = get_object_or_404(Schedule, pk=id)
    return render(request, 'scheduling/schedule_detail.html', {'schedule': schedule})

# 3️⃣ Data JSON untuk kalender
def schedule_feed(request):
    schedules = Schedule.objects.all()
    data = [
        {
            "title": f"{s.category}: {s.team1} vs {s.team2}",
            # gabungkan date + time agar format ISO valid
            "start": f"{s.date}T{s.time}",
            "url": f"/scheduling/{s.id}/"
        }
        for s in schedules
    ]
    return JsonResponse(data, safe=False)

# def schedule_create(request):
#     if request.method == 'POST':
#         form = ScheduleForm(request.POST)
#         if form.is_valid():
#             schedule = form.save(commit=False)
#             schedule.organizer = request.user  # nanti ganti sesuai user login
#             schedule.save()
#             return redirect('scheduling:schedule_list')
#     else:
#         form = ScheduleForm()
#     return render(request, 'scheduling/schedule_form.html', {'form': form, 'title': 'Tambah Jadwal'})

def schedule_create(request):
    if request.method == "POST":
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            # Kalau user login → assign user, kalau tidak → None
            if request.user.is_authenticated:
                schedule.organizer = request.user
            else:
                schedule.organizer = None
            schedule.save()
            return redirect('scheduling:schedule_list')
    else:
        form = ScheduleForm()
    return render(request, 'scheduling/schedule_form.html', {'form': form, 'title': 'Tambah Jadwal'})

def schedule_update(request, id):
    schedule = get_object_or_404(Schedule, id=id)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            return redirect('scheduling:schedule_detail', id=id)
    else:
        form = ScheduleForm(instance=schedule)
    return render(request, 'scheduling/schedule_form.html', {'form': form, 'title': 'Edit Jadwal'})

def schedule_delete(request, id):
    schedule = get_object_or_404(Schedule, id=id)
    if request.method == 'POST':
        schedule.delete()
        return redirect('scheduling:schedule_list')
    return render(request, 'scheduling/schedule_confirm_delete.html', {'schedule': schedule})

def make_reviewable(request, id):
    schedule = get_object_or_404(Schedule, id=id)
    schedule.status = 'reviewable'
    schedule.save()
    return redirect('scheduling:schedule_detail', id=id)