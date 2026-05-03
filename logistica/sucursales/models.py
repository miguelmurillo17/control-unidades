from django.db import models


class Sucursal(models.Model):
    nombre     = models.CharField(max_length=100)
    ciudad     = models.CharField(max_length=100)
    tipo       = models.CharField(max_length=50, blank=True)
    activo     = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
