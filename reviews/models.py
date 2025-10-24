from django.db import models
from django.conf import settings
from scheduling.models import Schedule
from ticketing.models import Ticket

class Review(models.Model):
    RATING_CHOICES = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ]
    id = models.IntegerField(primary_key=True)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket,  on_delete=models.SET_NULL, null=True, blank=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)