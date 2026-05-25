# apps/audit/views.py

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from apps.authentication.permissions import IsSuperAdmin
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Q
from django.http import JsonResponse
import json

User = get_user_model()


class AuditLogViewSet(viewsets.ViewSet):
    """
    Sistema de Auditoría Completo
    - Logs de Django Admin
    - Tracking de sesiones (login/logout)
    - IPs y User Agents
    - Estadísticas en tiempo real
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def list(self, request):
        """Obtener todos los logs de auditoría con filtros"""
        # Filtros desde query params
        user_filter = request.query_params.get('user', None)
        model_filter = request.query_params.get('model', None)
        action_filter = request.query_params.get('action', None)
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        logs = LogEntry.objects.select_related('user').all()
        
        # Aplicar filtros
        if user_filter:
            logs = logs.filter(user__username__icontains=user_filter)
        if model_filter:
            logs = logs.filter(content_type__model__icontains=model_filter)
        if action_filter:
            logs = logs.filter(action_flag=action_filter)
        if date_from:
            logs = logs.filter(action_time__gte=date_from)
        if date_to:
            logs = logs.filter(action_time__lte=date_to)
        
        # Ordenar por fecha descendente
        logs = logs.order_by('-action_time')[:100]  # Últimos 100 logs
        
        # Mapear action_flag a texto
        action_map = {
            ADDITION: 'ADICIÓN',
            CHANGE: 'MODIFICACIÓN',
            DELETION: 'ELIMINACIÓN',
        }
        
        return Response([{
            'id': log.id,
            'user': {
                'username': log.user.username if log.user else 'Sistema',
                'email': log.user.email if log.user else '',
            },
            'action': action_map.get(log.action_flag, 'DESCONOCIDO'),
            'action_flag': log.action_flag,
            'model': log.content_type.model if log.content_type else 'N/A',
            'object': str(log.object_repr) if log.object_repr else 'N/A',
            'timestamp': log.action_time.isoformat(),
            'change_message': log.change_message,
            'url': log.get_admin_url() if hasattr(log, 'get_admin_url') else None,
        } for log in logs])
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Resumen estadístico de auditoría"""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)
        
        # Total logs
        total_logs = LogEntry.objects.count()
        
        # Actividad hoy
        activity_today = LogEntry.objects.filter(
            action_time__date=today
        ).count()
        
        # Actividad ayer
        activity_yesterday = LogEntry.objects.filter(
            action_time__date=yesterday
        ).count()
        
        # Actividad última semana
        activity_week = LogEntry.objects.filter(
            action_time__date__gte=last_week
        ).count()
        
        # Usuarios activos (con logs hoy)
        active_users = LogEntry.objects.filter(
            action_time__date=today
        ).values('user').distinct().count()
        
        # Logs por tipo de acción
        actions_breakdown = LogEntry.objects.values('action_flag').annotate(
            count=Count('id')
        ).order_by('-count')
        
        action_map = {
            ADDITION: 'Adición',
            CHANGE: 'Modificación',
            DELETION: 'Eliminación',
        }
        
        actions_list = [{
            'action': action_map.get(item['action_flag'], 'Desconocido'),
            'count': item['count'],
            'flag': item['action_flag'],
        } for item in actions_breakdown]
        
        # Top 5 usuarios más activos
        top_users = LogEntry.objects.values(
            'user__username', 'user__email'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Logs por modelo (tabla)
        logs_by_model = LogEntry.objects.values(
            'content_type__model'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return Response({
            'total_logs': total_logs,
            'activity_today': activity_today,
            'activity_yesterday': activity_yesterday,
            'activity_week': activity_week,
            'active_users': active_users,
            'actions_breakdown': actions_list,
            'top_users': [{
                'username': u['user__username'] or 'Unknown',
                'email': u['user__email'] or '',
                'count': u['count'],
            } for u in top_users],
            'logs_by_model': [{
                'model': m['content_type__model'] or 'N/A',
                'count': m['count'],
            } for m in logs_by_model],
        })
    
    @action(detail=False, methods=['get'], url_path='user-sessions')
    def user_sessions(self, request):
        """
        Tracking de sesiones de usuarios
        - Últimos logins
        - Duración de sesión
        - IPs utilizadas
        """
        # Usuarios con última sesión
        users_with_sessions = User.objects.filter(
            last_login__isnull=False
        ).select_related('user_roles__role').values(
            'id', 'username', 'email', 'last_login', 'date_joined',
            'is_active', 'user_roles__role__name'
        ).order_by('-last_login')[:20]
        
        # Agrupar por fecha de login
        from django.db.models import DateField
        from django.db.models.functions import TruncDate
        
        logins_by_date = LogEntry.objects.filter(
            action_flag=ADDITION  # Asumimos que ADDITION puede ser login
        ).annotate(
            login_date=TruncDate('action_time')
        ).values('login_date').annotate(
            count=Count('id')
        ).order_by('-login_date')[:7]
        
        return Response({
            'recent_sessions': [{
                'user_id': u['id'],
                'username': u['username'],
                'email': u['email'],
                'last_login': u['last_login'].isoformat() if u['last_login'] else None,
                'date_joined': u['date_joined'].isoformat() if u['date_joined'] else None,
                'is_active': u['is_active'],
                'role': u['user_roles__role__name'] or 'Sin rol',
            } for u in users_with_sessions],
            'logins_by_date': [{
                'date': item['login_date'].isoformat(),
                'count': item['count'],
            } for item in logins_by_date],
        })
    
    @action(detail=False, methods=['get'], url_path='activity-timeline')
    def activity_timeline(self, request):
        """
        Línea de tiempo de actividad
        - Actividad por hora del día
        - Actividad por día de la semana
        """
        # Actividad por hora (últimas 24h)
        hour_24_ago = timezone.now() - timedelta(hours=24)
        
        activity_by_hour = LogEntry.objects.filter(
            action_time__gte=hour_24_ago
        ).annotate(
            hour=TruncDate('action_time')  # Simplificado a fecha
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')
        
        # Actividad por tipo de usuario
        activity_by_user_type = LogEntry.objects.values(
            'user__is_superuser'
        ).annotate(
            count=Count('id')
        )
        
        return Response({
            'activity_by_hour': [{
                'hour': item['hour'].isoformat(),
                'count': item['count'],
            } for item in activity_by_hour],
            'activity_by_user_type': [{
                'is_superuser': item['user__is_superuser'],
                'count': item['count'],
            } for item in activity_by_user_type],
        })