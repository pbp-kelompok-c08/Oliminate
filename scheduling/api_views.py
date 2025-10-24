from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from datetime import datetime
from .models import Schedule

def _parse_date(date_str: str):
    """Parse 'YYYY-MM-DD' jadi date Python"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        # fallback: kalau format aneh (mis. 'MM/DD/YYYY')
        try:
            return datetime.strptime(date_str, "%m/%d/%Y").date()
        except Exception:
            raise ValueError("Format tanggal tidak valid.")


def _parse_time(time_str: str):
    """Parse 'HH:MM' atau 'HH:MM:SS' jadi time Python"""
    if not time_str:
        return None
    try:
        return datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        try:
            return datetime.strptime(time_str, "%H:%M:%S").time()
        except Exception:
            raise ValueError("Format jam tidak valid.")


def _fmt_date(d):
    if hasattr(d, "strftime"):
        return d.strftime("%Y-%m-%d")
    return str(d)


def _fmt_time(t):
    if hasattr(t, "strftime"):
        return t.strftime("%H:%M")
    return str(t)


def _serialize(schedule: Schedule):
    return {
        "id": schedule.id,
        "category": schedule.category,
        "team1": schedule.team1,
        "team2": schedule.team2,
        "location": schedule.location,
        "date": _fmt_date(schedule.date),
        "time": _fmt_time(schedule.time),
        "caption": schedule.caption or "",
        "image_url": schedule.image_url or "",
        "status": schedule.status,
        "organizer": schedule.organizer.username if schedule.organizer else "-",
    }

@require_http_methods(["GET"])
def api_list_schedules(request):
    f = request.GET.get("filter", "all")
    qs = Schedule.objects.exclude(status='reviewable').order_by("date", "time")
    if f == "mine" and request.user.is_authenticated:
        qs = qs.filter(organizer=request.user)

    items = [_serialize(s) for s in qs]
    return JsonResponse({"ok": True, "count": len(items), "items": items})


@login_required
@require_http_methods(["POST"])
def api_create_schedule(request):
    """Buat jadwal baru (khusus role organizer)"""
    if getattr(request.user, "role", None) != "organizer":
        return HttpResponseForbidden("Hanya organizer yang dapat membuat jadwal.")

    data = request.POST
    try:
        date_val = _parse_date(data.get("date"))
        time_val = _parse_time(data.get("time"))

        s = Schedule.objects.create(
            category=data.get("category", "").strip(),
            team1=data.get("team1", "").strip(),
            team2=data.get("team2", "").strip(),
            location=data.get("location", "").strip(),
            date=date_val,
            time=time_val,
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
    s = get_object_or_404(Schedule, id=id)

    if s.organizer != request.user:
        return HttpResponseForbidden("Tidak boleh mengedit jadwal milik orang lain.")

    data = request.POST
    try:
        for field in ["category", "team1", "team2", "location", "caption", "image_url", "status"]:
            if field in data:
                val = data.get(field)
                setattr(s, field, val if val != "" else None)

        # Parsing khusus untuk date/time
        if "date" in data:
            s.date = _parse_date(data.get("date"))
        if "time" in data:
            s.time = _parse_time(data.get("time"))

        s.save()
        return JsonResponse({"ok": True, "item": _serialize(s)})
    except Exception as e:
        return JsonResponse({"ok": False, "errors": {"__all__": str(e)}})


@login_required
@require_http_methods(["POST"])
def api_delete_schedule(request, id):
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
    s = get_object_or_404(Schedule, id=id)

    if s.organizer != request.user:
        return HttpResponseForbidden("Tidak boleh menandai jadwal milik orang lain.")

    if s.status != "reviewable":
        s.status = "reviewable"
        s.save()
        return JsonResponse({"ok": True, "item": _serialize(s), "message": "Jadwal ditandai reviewable."})
    else:
        return JsonResponse({"ok": True, "item": _serialize(s), "message": "Jadwal sudah reviewable sebelumnya."})
    
@login_required
@require_http_methods(["POST"])
def api_mark_completed(request, id):
    """
    POST /scheduling/api/<id>/complete/
    Hanya organizer pemilik yang boleh menandai 'completed'.
    Hanya boleh dari status 'upcoming' -> 'completed'.
    """
    s = get_object_or_404(Schedule, id=id)

    if s.organizer != request.user:
        return HttpResponseForbidden("Tidak boleh menandai jadwal milik orang lain.")

    if s.status == "reviewable":
        return JsonResponse({"ok": False, "errors": {"__all__": "Jadwal sudah reviewable."}})

    if s.status == "completed":
        return JsonResponse({"ok": True, "item": _serialize(s), "message": "Jadwal sudah completed."})

    # dari 'upcoming' -> 'completed'
    s.status = "completed"
    s.save()
    return JsonResponse({"ok": True, "item": _serialize(s), "message": "Jadwal ditandai completed."})
