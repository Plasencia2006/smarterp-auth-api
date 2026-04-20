from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'estado', 'is_super_admin', 'is_active']
    list_filter = ['estado', 'is_super_admin']
    search_fields = ['email', 'username']
    ordering = ['-date_joined']
    fieldsets = UserAdmin.fieldsets + (
        ('SmartERP', {'fields': ('estado', 'is_super_admin')}),
    )