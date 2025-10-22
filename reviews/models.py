from django.db import models
from django.conf import settings
from scheduling.models import Schedule
# from ticketing.models import Ticket

class Review(models.Model):
    id = models.IntegerField(primary_key=True)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    # ticket = models.ForeignKey(Ticket, null=True, blank=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField()  # 1-5 (validasi di form)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)