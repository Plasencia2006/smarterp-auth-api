# apps/business/models.py

from django.db import models
from django.conf import settings
import uuid


class Business(models.Model):
    """Modelo de Negocio/Empresa"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, verbose_name="Nombre del Negocio")
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=20, default='RETAIL')
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_businesses',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = "Negocio"
        verbose_name_plural = "Negocios"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Membership(models.Model):
    """
    Relación Usuario-Negocio (Roles y Permisos)
    ✅ Corregido: Coincide exactamente con tu BD (sin assigned_by)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='business_memberships'
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    
    # Roles disponibles
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Propietario'
        ADMIN = 'ADMIN', 'Administrador'
        MANAGER = 'MANAGER', 'Gerente'
        VENDEDOR = 'VENDEDOR', 'Vendedor'
        CLIENTE = 'CLIENTE', 'Cliente'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENTE
    )
    
    # ✅ Mantenemos permissions porque tu BD tiene la columna 'permissions'
    permissions = models.JSONField(default=list, blank=True, null=True)
    
    # Estado
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    # ❌ ELIMINADO: assigned_by (no existe en tu BD)
    
    class Meta:
        verbose_name = "Membresía"
        verbose_name_plural = "Membresías"
        unique_together = ['user', 'business']
        ordering = ['business__name', 'role']
    
    def __str__(self):
        return f"{self.user.email} - {self.business.name} ({self.role})"