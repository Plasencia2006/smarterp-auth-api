"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include

from apps.analytics.views import GlobalStatsAPIView, SystemActivityAPIView
from apps.audit.views import AuditLogViewSet
from apps.backups.views import BackupViewSet

urlpatterns = [
    # ─────────────────────────────────────────────────────────────
    # 📦 ADMIN
    # ─────────────────────────────────────────────────────────────
    path('admin/', admin.site.urls),
    
    # ─────────────────────────────────────────────────────────────
    # 🔐 AUTH & SUPER ADMIN
    # ─────────────────────────────────────────────────────────────
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/', include('superadmin.urls')),
    
    # ─────────────────────────────────────────────────────────────
    # 🎯 BUSINESS MODULE (ORDEN CRÍTICO)
    # ─────────────────────────────────────────────────────────────
    
    # 1️⃣ PRIMERO: Rutas específicas de Roles y Permisos
    #    (Para que no sean capturadas por rutas genéricas)
    path('api/v1/business/', include('apps.business_roles.urls')),
    
    # 2️⃣ DESPUÉS: Rutas principales de Negocios
    #    (BusinessViewSet, MembershipViewSet, BusinessUserViewSet)
    path('api/v1/business/', include('apps.business.urls')),
    
    # ─────────────────────────────────────────────────────────────
    # 📊 ANALYTICS / AUDIT / BACKUPS (Endpoints sueltos)
    # ─────────────────────────────────────────────────────────────
    path('api/v1/backups/<str:pk>/restore/', BackupViewSet.as_view({'post': 'restore'})),
    path('api/v1/backups/<str:pk>/download/', BackupViewSet.as_view({'get': 'download'})),
    path('api/v1/analytics/global-stats/', GlobalStatsAPIView.as_view()),
    path('api/v1/analytics/activity/', SystemActivityAPIView.as_view()),
    path('api/v1/audit-logs/', AuditLogViewSet.as_view({'get': 'list'})),
    path('api/v1/audit-logs/summary/', AuditLogViewSet.as_view({'get': 'summary'})),
    path('api/v1/backups/', include('apps.backups.urls')),
]