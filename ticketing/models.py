from django.db import models
# from scheduling.models import Schedule
# from users.models import User

# Create your models here.
class Ticket(models.Model):
    id = models.AutoField(primary_key=True)
    # schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='tickets')
    # buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)
    qr_code = models.CharField(max_length=255, blank=True, null=True)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.buyer.username} ({'Used' if self.is_used else 'Unused'})"