from django.db import models

# Create your models here.
import uuid
from django.db import models

class BusinessPermission(models.Model):
    """Permisos granulares del sistema"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    module = models.CharField(max_length=50)  # SALES, INVENTORY, USERS, etc.
    description = models.TextField(blank=True)

    class Meta:
        app_label = 'business_roles'  # CRÍTICO para evitar errores de migración
        ordering = ['module', 'code']

    def __str__(self):
        return f"{self.code} ({self.name})"


class BusinessRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey('business.Business', on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField('BusinessPermission', related_name='roles', blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # 🔴 ESTE CAMPO DEBE EXISTIR

    class Meta:
        app_label = 'business_roles'
        unique_together = ('business', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.business.name}"