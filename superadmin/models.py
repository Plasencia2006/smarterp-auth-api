from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    ROLE_CHOICES = (
        ('SUPER_ADMIN', 'Super Admin'),
        ('BUSINESS_OWNER', 'Business Owner'),
        ('MANAGER', 'Manager'),
        ('EMPLOYEE', 'Employee'),
    )

    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default='EMPLOYEE'
    )

    is_super_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username