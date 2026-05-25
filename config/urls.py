"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from apps.analytics.views import GlobalStatsAPIView, SystemActivityAPIView
from apps.audit.views import AuditLogViewSet
from apps.backups.views import BackupViewSet

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/business/', include('apps.business.urls')),
    path('api/v1/', include('superadmin.urls')),
    
        path('api/v1/backups/<str:pk>/restore/', BackupViewSet.as_view({'post': 'restore'})),
    path('api/v1/backups/<str:pk>/download/', BackupViewSet.as_view({'get': 'download'})),
    path('api/v1/analytics/global-stats/', GlobalStatsAPIView.as_view()),
    path('api/v1/analytics/activity/', SystemActivityAPIView.as_view()),
    path('api/v1/audit-logs/', AuditLogViewSet.as_view({'get': 'list'})),
    path('api/v1/audit-logs/summary/', AuditLogViewSet.as_view({'get': 'summary'})),
    path('api/v1/backups/', include('apps.backups.urls')),
]
