import uuid
from django.db import models
from django.contrib.auth.models import User

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
    price = models.IntegerField(default=0)
    stock = models.IntegerField(default=0)
    description = models.TextField()
    image_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name
    
