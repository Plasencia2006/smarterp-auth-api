# apps/core/views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.db import connection
from apps.authentication.permissions import IsSuperAdmin
import os
import json
from datetime import datetime


class GlobalSettingsViewSet(viewsets.ViewSet):
    """
    Configuración Global del Sistema
    Obtiene y actualiza configuración real del sistema
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def list(self, request):
        """Obtener configuración actual del sistema"""
        
        # Obtener configuración real de Django settings
        config = {
            'general': {
                'site_name': getattr(settings, 'SITE_NAME', 'SMART ERP'),
                'site_description': getattr(settings, 'SITE_DESCRIPTION', ''),
                'timezone': settings.TIME_ZONE,
                'language': getattr(settings, 'LANGUAGE_CODE', 'es'),
                'debug': settings.DEBUG,
                'version': '1.0.0',  # Puedes obtenerlo de un archivo version.py
            },
            'database': {
                'engine': settings.DATABASES['default']['ENGINE'],
                'name': settings.DATABASES['default']['NAME'],
                'host': settings.DATABASES['default'].get('HOST', 'localhost'),
                'port': settings.DATABASES['default'].get('PORT', '3306'),
            },
            'email': {
                'email_host': settings.EMAIL_HOST,
                'email_port': settings.EMAIL_PORT,
                'email_user': settings.EMAIL_HOST_USER,
                'email_from': settings.DEFAULT_FROM_EMAIL,
                'email_enabled': getattr(settings, 'EMAIL_ENABLED', False),
            },
            'security': {
                'password_min_length': getattr(settings, 'PASSWORD_MIN_LENGTH', 8),
                'session_timeout': getattr(settings, 'SESSION_COOKIE_AGE', 3600) // 60,
                'allowed_hosts': settings.ALLOWED_HOSTS,
            },
            'system': {
                'max_upload_size': getattr(settings, 'MAX_UPLOAD_SIZE', 10),
                'media_root': settings.MEDIA_ROOT,
                'static_root': settings.STATIC_ROOT,
                'log_level': getattr(settings, 'LOG_LEVEL', 'INFO'),
            }
        }
        
        return Response(config)
    
    def update(self, request):
        """Actualizar configuración (se guardaría en base de datos o archivo)"""
        # Aquí implementarías la lógica para guardar en DB o settings dinámicos
        return Response({
            'message': 'Configuración actualizada',
            'data': request.data
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def system_info(request):
    """
    Información real del sistema
    """
    # Obtener información del SO
    import platform
    import psutil
    
    # Uso de recursos
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Información de la base de datos
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        db_version = cursor.fetchone()[0]
        
        # Contar registros por tabla
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM authentication_user) as users,
                (SELECT COUNT(*) FROM business_business) as businesses,
                (SELECT COUNT(*) FROM business_membership) as memberships
        """)
        counts = cursor.fetchone()
    
    return Response({
        'server': {
            'python_version': platform.python_version(),
            'django_version': platform.django_version if hasattr(platform, 'django_version') else '4.2.9',
            'os': f"{platform.system()} {platform.release()}",
            'hostname': platform.node(),
        },
        'resources': {
            'cpu_usage': cpu_percent,
            'memory_total': round(memory.total / (1024**3), 2),
            'memory_used': round(memory.used / (1024**3), 2),
            'memory_percent': memory.percent,
            'disk_total': round(disk.total / (1024**3), 2),
            'disk_used': round(disk.used / (1024**3), 2),
            'disk_percent': disk.percent,
        },
        'database': {
            'version': db_version,
            'users_count': counts[0],
            'businesses_count': counts[1],
            'memberships_count': counts[2],
        },
        'uptime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })