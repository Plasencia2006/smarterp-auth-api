from django.contrib import admin
from .models import Business, Membership


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'owner', 'is_active', 'created_at']
    list_filter = ['type', 'is_active']
    search_fields = ['name']


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'business', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active']