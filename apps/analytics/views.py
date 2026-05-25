# apps/analytics/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.authentication.permissions import IsSuperAdmin
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from apps.business.models import Business, Membership
from apps.authentication.models import CustomUser
from collections import defaultdict


class GlobalStatsAPIView(APIView):
    """
    Estadísticas globales del sistema
    Versión compatible con MySQL sin timezone tables
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def get(self, request):
        # Totales generales
        total_users = CustomUser.objects.count()
        active_users = CustomUser.objects.filter(is_active=True).count()
        total_businesses = Business.objects.count()
        active_businesses = Business.objects.filter(is_active=True).count()
        total_memberships = Membership.objects.count()
        
        # Usuarios por estado (usando valores reales del modelo)
        users_by_status = CustomUser.objects.values('is_active').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Transformar a formato legible
        users_by_status_list = [
            {
                'estado': 'ACTIVO' if item['is_active'] else 'INACTIVO',
                'count': item['count']
            }
            for item in users_by_status
        ]
        
        # Negocios por tipo
        businesses_by_type = Business.objects.values('type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Crecimiento mensual de usuarios (procesado en Python para evitar timezone issues)
        # Obtener usuarios de los últimos 6 meses
        six_months_ago = timezone.now() - timedelta(days=180)
        recent_users = CustomUser.objects.filter(
            date_joined__gte=six_months_ago
        ).values('date_joined')
        
        # Agrupar por mes manualmente en Python
        users_by_month = defaultdict(int)
        for user in recent_users:
            date = user['date_joined']
            if date:
                # Usar solo año y mes, ignorar timezone
                month_key = date.strftime('%Y-%m')
                users_by_month[month_key] += 1
        
        # Convertir a lista ordenada
        users_growth = [
            {'month': month, 'count': count}
            for month, count in sorted(users_by_month.items())
        ][-6:]  # Últimos 6 meses
        
        # Top negocios por miembros
        top_businesses = Business.objects.annotate(
            member_count=Count('memberships')
        ).order_by('-member_count')[:5]
        
        return Response({
            'totals': {
                'users': total_users,
                'active_users': active_users,
                'businesses': total_businesses,
                'active_businesses': active_businesses,
                'memberships': total_memberships,
            },
            'users_by_status': users_by_status_list,
            'businesses_by_type': list(businesses_by_type),
            'users_growth': users_growth,
            'top_businesses': [
                {'name': b.name, 'members': b.member_count, 'type': b.type}
                for b in top_businesses
            ],
        })


class SystemActivityAPIView(APIView):
    """
    Actividad reciente del sistema
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def get(self, request):
        # Últimos usuarios registrados
        recent_users = CustomUser.objects.order_by('-date_joined')[:10].values(
            'id', 'username', 'email', 'date_joined', 'is_active'
        )
        
        # Últimos negocios creados
        recent_businesses = Business.objects.order_by('-created_at')[:10].values(
            'id', 'name', 'type', 'created_at', 'owner__username'
        )
        
        # Usuarios que han iniciado sesión recientemente
        recent_logins = CustomUser.objects.filter(
            last_login__isnull=False
        ).order_by('-last_login')[:10].values(
            'id', 'username', 'last_login'
        )
        
        # Formatear fechas para evitar problemas de timezone
        def safe_date(value):
            if value and hasattr(value, 'isoformat'):
                return value.isoformat()
            return value
        
        return Response({
            'recent_users': [
                {**u, 'date_joined': safe_date(u['date_joined'])} 
                for u in recent_users
            ],
            'recent_businesses': [
                {**b, 'created_at': safe_date(b['created_at'])} 
                for b in recent_businesses
            ],
            'recent_logins': [
                {**l, 'last_login': safe_date(l['last_login'])} 
                for l in recent_logins
            ],
        })

# apps/analytics/views.py

class GlobalStatsAPIView(APIView):
    """
    Estadísticas globales del sistema
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):

        # =========================
        # Totales generales
        # =========================
        total_users = CustomUser.objects.count()

        active_users = CustomUser.objects.filter(
            estado='ACTIVO'
        ).count()

        inactive_users = CustomUser.objects.exclude(
            estado='ACTIVO'
        ).count()

        total_businesses = Business.objects.count()

        active_businesses = Business.objects.filter(
            is_active=True
        ).count()

        total_memberships = Membership.objects.count()

        # =========================
        # Usuarios por estado
        # =========================
        users_by_status_query = (
            CustomUser.objects
            .values('estado')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        users_by_status_list = [
            {
                'estado': item['estado'] or 'SIN_ESTADO',
                'count': item['count']
            }
            for item in users_by_status_query
            if item['count'] > 0
        ]

        # =========================
        # Negocios por tipo
        # =========================
        businesses_by_type = (
            Business.objects
            .values('type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # =========================
        # Crecimiento mensual
        # =========================
        six_months_ago = timezone.now() - timedelta(days=180)

        recent_users = (
            CustomUser.objects
            .filter(date_joined__gte=six_months_ago)
            .values('date_joined')
        )

        users_by_month = defaultdict(int)

        for user in recent_users:
            date = user.get('date_joined')

            if date:
                month_key = date.strftime('%Y-%m')
                users_by_month[month_key] += 1

        users_growth = [
            {
                'month': month,
                'count': count
            }
            for month, count in sorted(users_by_month.items())
        ][-6:]

        # =========================
        # Top negocios
        # =========================
        top_businesses = (
            Business.objects
            .annotate(member_count=Count('memberships'))
            .order_by('-member_count')[:5]
        )

        # =========================
        # Response
        # =========================
        return Response({
            'totals': {
                'users': total_users,
                'active_users': active_users,
                'inactive_users': inactive_users,
                'businesses': total_businesses,
                'active_businesses': active_businesses,
                'memberships': total_memberships,
            },

            'users_by_status': users_by_status_list,

            'businesses_by_type': list(businesses_by_type),

            'users_growth': users_growth,

            'top_businesses': [
                {
                    'name': business.name,
                    'members': business.member_count,
                    'type': business.type
                }
                for business in top_businesses
            ],
        })