# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(max_length=255, unique=True)

    class Role(models.TextChoices):
        USER = 'user', 'User'
        ORGANIZER = 'organizer', 'Organizer'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER
    )
    
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='fotoUser', null=True, blank=True)
    fakultas = models.CharField(max_length=100, null=True, blank=True)
