import uuid
from django.db import models
from users.models import User

class Merchandise(models.Model):
    CATEGORY_CHOICES = [
        ('t-shirt', 'T-Shirt'),
        ('sweater', 'Sweater'),
        ('bandana', 'Bandana'),
        ('hat', 'Hat'),
        ('scarf', 'Scarf'),
        ('totebag', 'Totebag'),
        ('handfan', 'Handfan'),
        ('sticker', 'Sticker'),
        ('keychain', 'Keychain'),
        ('lanyard', 'Lanyard')
    ]

    organizer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='merchandises')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)
    description = models.TextField()
    image_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name
    
class Cart(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('checked_out', 'Checked Out'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total_price(self):
        return sum(item.subtotal for item in self.items.all())

    def __str__(self):
        return f"Cart {self.id} ({self.user}) - {self.status}"


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    merchandise = models.ForeignKey(Merchandise, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_snapshot = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        unique_together = ('cart', 'merchandise')

    def save(self, *args, **kwargs):
        if self.price_snapshot is None and self.merchandise:
            self.price_snapshot = self.merchandise.price
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return (self.price_snapshot or 0) * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.merchandise.name} in cart {self.cart.id}"