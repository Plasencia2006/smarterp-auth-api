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

User = get_user_model()


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
        
        membership, created = Membership.objects.update_or_create(
            user=user,
            business=business,
            defaults={
                'role': role,
                'is_active': True
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


# =============================================================================
# ✅ NUEVO: GESTIÓN DE USUARIOS DEL NEGOCIO CON ASIGNACIÓN DE ROLES
# =============================================================================
class BusinessUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Permite al Admin ver usuarios de su negocio y asignarles roles.
    """
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Solo devuelve usuarios que pertenecen al mismo negocio que el Admin"""
        user = self.request.user
        
        try:
            membership = Membership.objects.filter(user=user, is_active=True).first()
            if membership:
                user_ids = Membership.objects.filter(
                    business=membership.business, 
                    is_active=True
                ).values_list('user_id', flat=True)
                return User.objects.filter(id__in=user_ids).select_related('profile')
        except Exception as e:
            print(f"❌ Error getting users: {e}")
            
        return User.objects.none()
    
    @action(detail=True, methods=['post'], url_path='assign_role')
    def assign_role(self, request, pk=None):
        """
        Asigna un rol a un empleado del negocio.
        Body: {"role_id": "uuid-del-rol"}
        """
        employee = self.get_object()
        role_id = request.data.get('role_id')
        
        if not role_id:
            return Response(
                {'error': 'Se requiere role_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.business_roles.models import BusinessRole
            
            role = BusinessRole.objects.get(id=role_id)
            
            # Seguridad: Verificar que el Admin pertenece al mismo negocio que el rol
            admin_membership = Membership.objects.filter(
                user=request.user, 
                is_active=True
            ).first()
            
            if not admin_membership or role.business != admin_membership.business:
                return Response(
                    {'error': 'No autorizado para asignar este rol'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Asignar rol al empleado
            employee.business_roles.add(role)
            
            return Response(
                {
                    'message': f'Rol "{role.name}" asignado correctamente a {employee.email}',
                    'role': {
                        'id': str(role.id),
                        'name': role.name
                    }
                }, 
                status=status.HTTP_200_OK
            )
            
        except BusinessRole.DoesNotExist:
            return Response(
                {'error': 'Rol no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='remove_role')
    def remove_role(self, request, pk=None):
        """
        Remueve un rol de un empleado del negocio.
        Body: {"role_id": "uuid-del-rol"}
        """
        employee = self.get_object()
        role_id = request.data.get('role_id')
        
        if not role_id:
            return Response(
                {'error': 'Se requiere role_id'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.business_roles.models import BusinessRole
            
            role = BusinessRole.objects.get(id=role_id)
            
            # Verificar permisos
            admin_membership = Membership.objects.filter(
                user=request.user, 
                is_active=True
            ).first()
            
            if not admin_membership or role.business != admin_membership.business:
                return Response(
                    {'error': 'No autorizado'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            employee.business_roles.remove(role)
            
            return Response(
                {
                    'message': f'Rol "{role.name}" removido de {employee.email}',
                    'role': {
                        'id': str(role.id),
                        'name': role.name
                    }
                }, 
                status=status.HTTP_200_OK
            )
            
        except BusinessRole.DoesNotExist:
            return Response(
                {'error': 'Rol no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='with-roles')
    def users_with_roles(self, request):
        """
        Obtiene todos los usuarios del negocio con sus roles asignados.
        """
        users = self.get_queryset()
        data = []
        
        for user in users:
            user_roles = user.business_roles.all().prefetch_related('permissions')
            roles_data = [
                {
                    'id': str(role.id),
                    'name': role.name,
                    'permissions': [
                        {'code': p.code, 'name': p.name, 'module': p.module}
                        for p in role.permissions.all()
                    ]
                }
                for role in user_roles
            ]
            
            data.append({
                'id': str(user.id),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'roles': roles_data
            })
        
        return Response(data, status=status.HTTP_200_OK)