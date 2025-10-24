import pytest
from datetime import date, time, timedelta, datetime

from django.utils import timezone
from django.contrib.auth import get_user_model

from scheduling.models import Schedule 


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(username="u", email="u@example.com", password="x")


@pytest.fixture
def today():
    return timezone.localdate()


def make_schedule(**kwargs):
    defaults = dict(
        category="Soccer",
        team1="A",
        team2="B",
        location="Stadium",
        date=timezone.localdate(),
        time=time(12, 0),
        status="upcoming",
    )
    defaults.update(kwargs)
    return Schedule.objects.create(**defaults)


@pytest.mark.django_db
def test_str_representation(today):
    s = make_schedule(category="Basket", team1="X", team2="Y", date=today)
    assert str(s) == f"Basket: X vs Y ({today})"


@pytest.mark.django_db
def test_default_status_is_upcoming(today):
    s = make_schedule(date=today)
    assert s.status == "upcoming"


@pytest.mark.django_db
def test_meta_ordering_by_date_then_time(today):
    s3 = make_schedule(date=today + timedelta(days=1), time=time(9, 0))
    s1 = make_schedule(date=today, time=time(8, 0))
    s2 = make_schedule(date=today, time=time(18, 0))

    ids = list(Schedule.objects.values_list("id", flat=True))
    assert ids == [s1.id, s2.id, s3.id]


@pytest.mark.django_db
def test_get_datetime_is_naive(today):
    s = make_schedule(date=today, time=time(7, 30))
    dt = s.get_datetime()
    # Sesuai model saat ini: dt NAIVE (tanpa tzinfo)
    assert not timezone.is_aware(dt)


@pytest.mark.django_db
def test_is_past_raises_typeerror(monkeypatch, today):
    # Bekukan "sekarang" ke datetime AWARE → membandingkan dengan NAIVE akan TypeError
    fixed_now = timezone.make_aware(datetime(2025, 1, 1, 12, 0), timezone.get_current_timezone())
    monkeypatch.setattr(timezone, "now", lambda: fixed_now)

    s = make_schedule(date=date(2025, 1, 1), time=time(11, 0))
    with pytest.raises(TypeError):
        _ = s.is_past


@pytest.mark.django_db
def test_mark_completed_raises_typeerror(monkeypatch):
    fixed_now = timezone.make_aware(datetime(2025, 1, 1, 12, 0), timezone.get_current_timezone())
    monkeypatch.setattr(timezone, "now", lambda: fixed_now)

    s = make_schedule(date=date(2025, 1, 1), time=time(10, 0), status="upcoming")
    with pytest.raises(TypeError):
        s.mark_completed()


@pytest.mark.django_db
def test_mark_reviewable_only_from_completed():
    s1 = make_schedule(status="upcoming")
    s1.mark_reviewable()
    s1.refresh_from_db()
    assert s1.status == "upcoming"

    s2 = make_schedule(status="completed")
    s2.mark_reviewable()
    s2.refresh_from_db()
    assert s2.status == "reviewable"

    s3 = make_schedule(status="reviewable")
    s3.mark_reviewable()
    s3.refresh_from_db()
    assert s3.status == "reviewable"


@pytest.mark.django_db
def test_organizer_set_null_when_user_deleted(user):
    s = make_schedule(organizer=user)
    assert s.organizer_id == user.id
    user.delete()
    s.refresh_from_db()
    assert s.organizer is None
