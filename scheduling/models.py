from django.db import models
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.models import User  # ✅ pakai user bawaan Django

class Schedule(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('completed', 'Completed'),
        ('reviewable', 'Reviewable'),
    ]


    organizer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,     #  ubah dari CASCADE jadi SET_NULL
        null=True, blank=True,         #  biar bisa kosong
        related_name="schedules"
    )

    category = models.CharField(max_length=50)           # Ex: "Futsal", "Badminton"
    team1 = models.CharField(max_length=100)
    team2 = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')

    image_url = models.URLField(blank=True, null=True)  
    caption = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return f"{self.category}: {self.team1} vs {self.team2} ({self.date})"

    # === Helper Methods ===
    def get_datetime(self):
        """Gabungkan tanggal dan waktu menjadi datetime Python."""
        return datetime.combine(self.date, self.time)

    def mark_completed(self):
        """Tandai event sebagai 'completed' jika sudah lewat waktunya."""
        if self.status == 'upcoming' and self.get_datetime() < timezone.now():
            self.status = 'completed'
            self.save()

    def mark_reviewable(self):
        """Organizer menandai bahwa event sudah bisa direview oleh penonton."""
        if self.status == 'completed':
            self.status = 'reviewable'
            self.save()

    @property
    def is_past(self):
        """True jika event sudah lewat (berdasarkan waktu sekarang)."""
        return self.get_datetime() < timezone.now()
