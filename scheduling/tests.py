import json
import pytest
from datetime import datetime, date, time

from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from scheduling.models import Schedule
from scheduling import views as v


@pytest.fixture
def User():
    return get_user_model()

@pytest.fixture
def user(db, User):
    return User.objects.create_user(username="u1", email="u1@example.com", password="x")

@pytest.fixture
def other_user(db, User):
    return User.objects.create_user(username="u2", email="u2@example.com", password="x")

@pytest.fixture
def login(client, user):
    client.force_login(user)
    return user

@pytest.fixture
def rf():
    return RequestFactory()

def mk_sched(**kw):
    defaults = dict(
        category="Soccer",
        team1="A",
        team2="B",
        location="Stadium",
        date=timezone.localdate(),
        time=time(9, 0),
        status="upcoming",
    )
    defaults.update(kw)
    return Schedule.objects.create(**defaults)


def test_parse_date_valid_iso():
    d = v._parse_date("2025-10-24")
    assert isinstance(d, date) and d.year == 2025 and d.month == 10 and d.day == 24

def test_parse_date_valid_fallback_mmddyyyy():
    d = v._parse_date("10/05/2025")
    assert isinstance(d, date) and d.year == 2025 and d.month == 10 and d.day == 5

def test_parse_date_invalid():
    with pytest.raises(ValueError):
        v._parse_date("24-10-2025")

def test_parse_time_valid_hhmm():
    t = v._parse_time("07:30")
    assert isinstance(t, time) and t.hour == 7 and t.minute == 30

def test_parse_time_valid_hhmmss():
    t = v._parse_time("07:30:45")
    assert isinstance(t, time) and t.hour == 7 and t.minute == 30 and t.second == 45

def test_parse_time_invalid():
    with pytest.raises(ValueError):
        v._parse_time("7.30")

def test_fmt_date_time_serialize(user):
    s = mk_sched(organizer=user, caption="hello", image_url="http://img")
    assert v._fmt_date(s.date) == s.date.strftime("%Y-%m-%d")
    assert v._fmt_time(s.time) == s.time.strftime("%H:%M")
    payload = v._serialize(s)
    assert payload["id"] == s.id
    assert payload["category"] == s.category
    assert payload["organizer"] == user.username
    assert payload["caption"] == "hello"
    assert payload["image_url"] == "http://img"
    assert payload["status"] == "upcoming"


@pytest.mark.django_db
def test_api_list_schedules_all(client, user, other_user):
    mk_sched(organizer=user, status="upcoming")
    mk_sched(organizer=other_user, status="completed")
    mk_sched(organizer=user, status="reviewable")
    url = reverse("scheduling:api_list_schedules")
    res = client.get(url)
    data = res.json()
    assert res.status_code == 200
    assert data["ok"] is True
    assert data["count"] == 2
    assert all(item["status"] != "reviewable" for item in data["items"])

@pytest.mark.django_db
def test_api_list_schedules_mine(client, login):
    me = login
    mk_sched(organizer=me, category="X")
    mk_sched(organizer=None, category="Y")
    mk_sched(organizer=None, status="reviewable", category="Z")
    url = reverse("scheduling:api_list_schedules")
    res = client.get(url, {"filter": "mine"})
    data = res.json()
    assert data["ok"] is True
    assert data["count"] == 1
    assert data["items"][0]["category"] == "X"
    assert data["items"][0]["organizer"] == me.username


@pytest.mark.django_db
def test_api_create_schedule_forbidden_without_organizer_role(client, login):
    url = reverse("scheduling:api_create_schedule")
    res = client.post(url, {
        "category": "Basket",
        "team1": "X",
        "team2": "Y",
        "location": "Hall",
        "date": "2025-01-01",
        "time": "10:00",
    })
    assert res.status_code == 403

@pytest.mark.django_db
def test_api_create_schedule_success_as_organizer(client, login, User, monkeypatch):
    monkeypatch.setattr(User, "role", "organizer", raising=False)
    url = reverse("scheduling:api_create_schedule")
    res = client.post(url, {
        "category": "Basket",
        "team1": "X",
        "team2": "Y",
        "location": "Hall",
        "date": "2025-01-01",
        "time": "10:00",
        "caption": "cap",
        "image_url": "http://x",
    })
    data = res.json()
    assert res.status_code == 200
    assert data["ok"] is True
    assert data["item"]["category"] == "Basket"
    assert data["item"]["organizer"] == "u1"


@pytest.mark.django_db
def test_api_update_schedule_owner_only(client, login, other_user):
    s = mk_sched(organizer=other_user, category="Old")
    url = reverse("scheduling:api_update_schedule", args=[s.id])
    res = client.post(url, {"category": "New"})
    assert res.status_code == 403

@pytest.mark.django_db
def test_api_update_schedule_success(client, login):
    s = mk_sched(organizer=login, category="Old", caption="")
    url = reverse("scheduling:api_update_schedule", args=[s.id])
    res = client.post(url, {
        "category": "New",
        "date": "2025-02-02",
        "time": "11:45:00",
        "caption": "c",
        "image_url": "",
        "status": "completed",
    })
    data = res.json()
    assert res.status_code == 200
    assert data["ok"] is True
    assert data["item"]["category"] == "New"
    assert data["item"]["date"] == "2025-02-02"
    assert data["item"]["time"] == "11:45"
    assert data["item"]["caption"] == "c"
    assert data["item"]["image_url"] == ""
    assert data["item"]["status"] == "completed"


@pytest.mark.django_db
def test_api_delete_schedule_owner_only(client, login, other_user):
    s = mk_sched(organizer=other_user)
    url = reverse("scheduling:api_delete_schedule", args=[s.id])
    res = client.post(url)
    assert res.status_code == 403

@pytest.mark.django_db
def test_api_delete_schedule_success(client, login):
    s = mk_sched(organizer=login)
    url = reverse("scheduling:api_delete_schedule", args=[s.id])
    res = client.post(url)
    data = res.json()
    assert res.status_code == 200
    assert data["ok"] is True
    assert not Schedule.objects.filter(id=s.id).exists()


@pytest.mark.django_db
def test_api_make_reviewable_owner_only(client, login, other_user):
    s = mk_sched(organizer=other_user, status="completed")
    url = reverse("scheduling:api_make_reviewable", args=[s.id])
    res = client.post(url)
    assert res.status_code == 403

@pytest.mark.django_db
def test_api_make_reviewable_transitions_and_idempotent(client, login):
    s = mk_sched(organizer=login, status="completed")
    url = reverse("scheduling:api_make_reviewable", args=[s.id])
    res1 = client.post(url)
    d1 = res1.json()
    assert res1.status_code == 200 and d1["ok"] is True
    assert d1["item"]["status"] == "reviewable"
    res2 = client.post(url)
    d2 = res2.json()
    assert res2.status_code == 200 and d2["ok"] is True
    assert d2["item"]["status"] == "reviewable"


@pytest.mark.django_db
def test_api_mark_completed_owner_only(client, login, other_user):
    s = mk_sched(organizer=other_user, status="upcoming")
    url = reverse("scheduling:api_mark_completed", args=[s.id])
    res = client.post(url)
    assert res.status_code == 403

@pytest.mark.django_db
def test_api_mark_completed_from_upcoming(client, login):
    s = mk_sched(organizer=login, status="upcoming")
    url = reverse("scheduling:api_mark_completed", args=[s.id])
    res = client.post(url)
    data = res.json()
    assert res.status_code == 200
    assert data["ok"] is True
    assert data["item"]["status"] == "completed"

@pytest.mark.django_db
def test_api_mark_completed_when_already_completed(client, login):
    s = mk_sched(organizer=login, status="completed")
    url = reverse("scheduling:api_mark_completed", args=[s.id])
    res = client.post(url)
    data = res.json()
    assert res.status_code == 200
    assert data["ok"] is True
    assert data["item"]["status"] == "completed"

@pytest.mark.django_db
def test_api_mark_completed_when_reviewable_should_fail(client, login):
    s = mk_sched(organizer=login, status="reviewable")
    url = reverse("scheduling:api_mark_completed", args=[s.id])
    res = client.post(url)
    data = res.json()
    assert res.status_code == 200
    assert data["ok"] is False
    assert "__all__" in data["errors"]


@pytest.mark.django_db
def test_schedule_feed(client, user):
    mk_sched(organizer=user, category="AA", team1="T1", team2="T2", date=date(2025, 1, 1), time=time(8, 0))
    url = reverse("scheduling:schedule_feed")
    res = client.get(url)
    assert res.status_code == 200
    arr = json.loads(res.content.decode())
    assert isinstance(arr, list) and len(arr) >= 1
    assert "title" in arr[0] and "start" in arr[0] and "url" in arr[0]


@pytest.mark.django_db
def test_schedule_list_view_filters_with_mine(monkeypatch, rf, user, other_user):
    mk_sched(organizer=other_user, status="upcoming")
    mine = mk_sched(organizer=user, status="upcoming")
    def fake_render(request, template, context):
        return v.JsonResponse({"cnt": context["schedules"].count(), "filter_type": context["filter_type"]})
    monkeypatch.setattr(v, "render", fake_render)
    req = rf.get(reverse("scheduling:schedule_list"), {"filter": "mine"})
    req.user = user
    res = v.schedule_list(req)
    data = res.json()
    assert data["cnt"] == 1 and data["filter_type"] == "mine"

@pytest.mark.django_db
def test_schedule_detail_view_returns_200(monkeypatch, rf, user):
    s = mk_sched(organizer=user)
    def fake_render(request, template, context):
        return v.JsonResponse({"id": context["schedule"].id})
    monkeypatch.setattr(v, "render", fake_render)
    req = rf.get(reverse("scheduling:schedule_detail", args=[s.id]))
    res = v.schedule_detail(req, s.id)
    data = res.json()
    assert data["id"] == s.id
