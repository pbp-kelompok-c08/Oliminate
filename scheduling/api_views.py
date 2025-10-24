from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import Schedule

def _serialize(schedule: Schedule):
    return {
        "id": schedule.id,
        "category": schedule.category,
        "team1": schedule.team1,
        "team2": schedule.team2,
        "location": schedule.location,
        "date": schedule.date.strftime("%Y-%m-%d"),
        "time": schedule.time.strftime("%H:%M"),
        "caption": schedule.caption or "",
        "image_url": schedule.image_url or "",
        "status": schedule.status,
        "organizer": schedule.organizer.username if schedule.organizer else "-",
    }

@login_required
@require_http_methods(["GET"])
def api_list_schedules(request):
    """
    GET /scheduling/api/list/?filter=all|mine
    - 'all'  : semua jadwal
    - 'mine' : hanya jadwal milik request.user (organizer)
    """
    f = request.GET.get("filter", "all")
    qs = Schedule.objects.exclude(status='reviewable').order_by("date", "time")
    if f == "mine":
        qs = qs.filter(organizer=request.user)

    items = [_serialize(s) for s in qs]
    return JsonResponse({"ok": True, "count": len(items), "items": items})

@login_required
@require_http_methods(["POST"])
def api_create_schedule(request):
    """
    POST /scheduling/api/create/
    Body: category, team1, team2, location, date(YYYY-MM-DD), time(HH:MM), caption?, image_url?
    HANYA role organizer yang boleh buat.
    """
    # validasi role
    if getattr(request.user, "role", None) != "organizer":
        return HttpResponseForbidden("Hanya organizer yang dapat membuat jadwal.")

    data = request.POST
    try:
        s = Schedule.objects.create(
            category=data.get("category", "").strip(),
            team1=data.get("team1", "").strip(),
            team2=data.get("team2", "").strip(),
            location=data.get("location", "").strip(),
            date=data.get("date"),   # "YYYY-MM-DD" — diterima oleh DateField
            time=data.get("time"),   # "HH:MM" — diterima oleh TimeField
            caption=(data.get("caption") or "").strip(),
            image_url=(data.get("image_url") or "").strip() or None,
            organizer=request.user,
        )
        return JsonResponse({"ok": True, "id": s.id, "item": _serialize(s)})
    except Exception as e:
        return JsonResponse({"ok": False, "errors": {"__all__": str(e)}})

@login_required
@require_http_methods(["POST"])
def api_update_schedule(request, id):
    """
    POST /scheduling/api/<id>/update/
    Body: field yang ingin diupdate (optional)
    HANYA pemilik (organizer schedule) yang boleh update.
    """
    s = get_object_or_404(Schedule, id=id)

    if s.organizer != request.user:
        return HttpResponseForbidden("Tidak boleh mengedit jadwal milik orang lain.")

    data = request.POST
    try:
        for field in ["category", "team1", "team2", "location", "date", "time", "caption", "image_url", "status"]:
            if field in data:
                val = data.get(field)
                setattr(s, field, val if val != "" else None)
        s.save()
        return JsonResponse({"ok": True, "item": _serialize(s)})
    except Exception as e:
        return JsonResponse({"ok": False, "errors": {"__all__": str(e)}})

@login_required
@require_http_methods(["POST"])
def api_delete_schedule(request, id):
    """
    POST /scheduling/api/<id>/delete/
    HANYA pemilik (organizer schedule) yang boleh hapus.
    """
    s = get_object_or_404(Schedule, id=id)

    if s.organizer != request.user:
        return HttpResponseForbidden("Tidak boleh menghapus jadwal milik orang lain.")

    try:
        s.delete()
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "errors": {"__all__": str(e)}})

@login_required
@require_http_methods(["POST"])
def api_make_reviewable(request, id):
    """
    POST /scheduling/api/<id>/make-reviewable/
    - Ubah status jadwal jadi 'reviewable'
    - Setelah itu, jadwal akan otomatis TIDAK muncul di halaman scheduling
      karena schedule_list & api_list_schedules mengecualikan status 'reviewable'.
    - Jadwal akan muncul di halaman 'review' (modul reviews kamu).
    - HANYA organizer pemilik jadwal yang boleh menandai.
    """
    s = get_object_or_404(Schedule, id=id)

    if s.organizer != request.user:
        return HttpResponseForbidden("Tidak boleh menandai jadwal milik orang lain.")

    if s.status != "reviewable":
        s.status = "reviewable"
        s.save()
        return JsonResponse({"ok": True, "item": _serialize(s), "message": "Jadwal ditandai reviewable."})
    else:
        return JsonResponse({"ok": True, "item": _serialize(s), "message": "Jadwal sudah reviewable sebelumnya."})
