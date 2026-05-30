import uuid
from django.db import models
from django.utils import timezone

class BusinessPermission(models.Model):
    """Permisos granulares del sistema"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    module = models.CharField(max_length=50)  # SALES, INVENTORY, USERS, etc.
    description = models.TextField(blank=True)

    class Meta:
        app_label = 'business_roles'
        ordering = ['module', 'code']

    def __str__(self):
        return f"{self.code} ({self.name})"


class BusinessRole(models.Model):
    """Roles personalizados por negocio"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey('business.Business', on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField('BusinessPermission', related_name='roles', blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'business_roles'
        unique_together = ('business', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.business.name}"


class BusinessUser(models.Model):
    """
    Usuario en el contexto de un negocio específico.
    Un CustomUser puede tener múltiples BusinessUser (si trabaja en varios negocios).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, related_name='business_users')
    business = models.ForeignKey('business.Business', on_delete=models.CASCADE, related_name='business_users')
    
    employee_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código Empleado")
    department = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    hire_date = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'business_roles'
        unique_together = ('user', 'business')
        ordering = ['user__first_name', 'user__last_name']
        verbose_name = 'Usuario del Negocio'
        verbose_name_plural = 'Usuarios del Negocio'

    def __str__(self):
        name = f"{self.user.first_name} {self.user.last_name}".strip()
        return f"{name or self.user.email} @ {self.business.name}"

    def deactivate(self):
        self.is_active = False
        self.left_at = timezone.now()
        self.save()


class BusinessUserRoleAssignment(models.Model):
    """
    Registro histórico y auditoría de asignación de roles.
    Permite rastrear quién asignó qué rol y cuándo.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business_user = models.ForeignKey(BusinessUser, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(BusinessRole, on_delete=models.CASCADE, related_name='user_assignments')
    
    assigned_by = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='role_assignments_made',
        verbose_name="Asignado por"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'business_roles'
        ordering = ['-assigned_at']
        verbose_name = 'Asignación de Rol'
        verbose_name_plural = 'Asignaciones de Rol'
        unique_together = ('business_user', 'role', 'is_active')  # Un rol activo por usuario

    def __str__(self):
        name = f"{self.business_user.user.first_name} {self.business_user.user.last_name}".strip()
        return f"{name or self.business_user.user.email} → {self.role.name}"

    def revoke(self):
        """Revocar esta asignación de rol"""
        self.is_active = False
        self.revoked_at = timezone.now()
        self.save()