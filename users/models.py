from django.db import models

# Create your models here.

class User(models.Model):
    username = models.CharField(max_length=150, unique=True, default='', blank=True)
    first_name = models.CharField(max_length=50, default='', blank=True)
    last_name = models.CharField(max_length=50, default='', blank=True)

    class Role(models.TextChoices):
        USER = 'user', 'User'
        ORGANIZER = 'organizer', 'Organizer'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER
    )
    
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255) 
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='fotoUser', null=True, blank=True)

    def __str__(self):
        return self.username