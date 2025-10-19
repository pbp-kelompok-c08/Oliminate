from django.db import models
import uuid

# Create your models here.

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)
    foto = models.ImageField(upload_to='fotoUser', blank=True)
    fakultas = models.CharField(max_length=100)

    def __str__(self):
        return self.name