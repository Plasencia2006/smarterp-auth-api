# apps/business/views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import Business, Membership
from .serializers import BusinessSerializer, MembershipSerializer, AssignAdminSerializer
from apps.authentication.permissions import IsSuperAdmin


class BusinessViewSet(viewsets.ModelViewSet):
    """CRUD de Negocios"""
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_super_admin', False) or user.is_superuser:
            return Business.objects.all().select_related('owner')
        return Business.objects.filter(
            memberships__user=user,
            memberships__is_active=True
        ).select_related('owner')
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class MembershipViewSet(viewsets.ModelViewSet):
    """Gestión de Membresías"""
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_super_admin', False) or user.is_superuser:
            # ❌ Eliminado 'assigned_by' del select_related
            return Membership.objects.all().select_related('user', 'business')
        return Membership.objects.filter(
            Q(business__owner=user) | 
            Q(business__memberships__user=user, business__memberships__role='ADMIN')
        ).select_related('user', 'business')
    
    @action(detail=False, methods=['post'], url_path='assign')
    def assign_admin(self, request):
        """Asignar usuario como administrador a un negocio"""
        serializer = AssignAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        business_id = serializer.validated_data['business_id']
        user_id = serializer.validated_data['user_id']
        role = serializer.validated_data['role']
        
        business = Business.objects.get(id=business_id)
        user = get_user_model().objects.get(id=user_id)
        
        # ✅ Actualización SIN assigned_by
        membership, created = Membership.objects.update_or_create(
            user=user,
            business=business,
            defaults={
                'role': role,
                'is_active': True
                # ❌ Eliminado: 'assigned_by': request.user
            }
        )
        
        response_serializer = self.get_serializer(membership)
        
        return Response(
            {
                'message': f'Usuario {"asignado" if created else "actualizado"} exitosamente como {role}',
                'membership': response_serializer.data
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='business/(?P<business_id>[^/.]+)/admins')
    def get_business_admins(self, request, business_id=None):
        """Obtener todos los administradores de un negocio"""
        memberships = Membership.objects.filter(
            business_id=business_id,
            is_active=True
        ).select_related('user')
        
        serializer = self.get_serializer(memberships, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='revoke')
    def revoke_access(self, request, pk=None):
        """Revocar acceso de un usuario a un negocio"""
        membership = self.get_object()
        membership.is_active = False
        membership.save(update_fields=['is_active'])
        
        return Response(
            {'message': 'Acceso revocado exitosamente'},
            status=status.HTTP_200_OK
        )