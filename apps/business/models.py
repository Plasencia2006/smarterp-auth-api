import uuid
from django.db import models
from django.conf import settings


class Business(models.Model):

    class BusinessType(models.TextChoices):
        TECH = 'TECH', 'Tecnologia'
        PHARMA = 'PHARMA', 'Farmacia'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    type = models.CharField(max_length=20, choices=BusinessType.choices)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='owned_businesses'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'business_business'

    def __str__(self):
        return f'{self.name} [{self.type}]'

    @property
    def requires_validation(self):
        return self.type == self.BusinessType.PHARMA


class Membership(models.Model):

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        VENDEDOR = 'VENDEDOR', 'Vendedor'
        CLIENTE = 'CLIENTE', 'Cliente'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships'
    )
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'business_membership'
        unique_together = [('user', 'business')]

    def __str__(self):
        return f'{self.user.email} -> {self.business.name} [{self.role}]'