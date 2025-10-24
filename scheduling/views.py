from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Schedule
from .forms import ScheduleForm
from django.shortcuts import redirect



def schedule_list(request):
    schedules = Schedule.objects.exclude(status='reviewable').order_by('date', 'time')
    return render(request, 'scheduling/schedule_list.html', {
        'schedules': schedules,
        'user': request.user  
    })

def schedule_detail(request, id):
    schedule = get_object_or_404(Schedule, pk=id)
    return render(request, 'scheduling/schedule_detail.html', {'schedule': schedule})


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

@login_required
def schedule_create(request):
    if request.user.role != 'organizer':
        messages.error(request, "Hanya pengguna dengan peran 'Organizer' yang dapat membuat jadwal.")
        return HttpResponseForbidden("Kamu tidak memiliki izin untuk membuat jadwal.")

    if request.method == "POST":
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.organizer = request.user  # organizer otomatis = user login
            schedule.save()
            messages.success(request, "Jadwal baru berhasil ditambahkan!")
            return redirect('scheduling:schedule_list')
    else:
        form = ScheduleForm()

    return render(request, 'scheduling/schedule_form.html', {
        'form': form,
        'title': 'Tambah Jadwal',
    })

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
    if schedule.status != 'reviewable':
        schedule.status = 'reviewable'
        schedule.save()
        messages.success(request, f"{schedule.category} sudah siap direview!")
    else:
        messages.info(request, f"{schedule.category} sudah direview sebelumnya.")
    return redirect('reviews:review_list')
