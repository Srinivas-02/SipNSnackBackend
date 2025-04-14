from django.db import models

class LocationModel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
