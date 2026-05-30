from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import BusinessPermission, BusinessRole, BusinessUser, BusinessUserRoleAssignment
from .serializers import BusinessPermissionSerializer, BusinessRoleSerializer, BusinessUserSerializer, BusinessUserRoleAssignmentSerializer
from apps.business.models import Membership
from apps.authentication.serializers import UserSerializer, RegisterSerializer

User = get_user_model()

def get_user_business_id(user):
    """Obtiene el business_id del usuario. Prioriza BusinessUser, fallback a Membership."""
    bu = BusinessUser.objects.filter(user=user, is_active=True).select_related('business').first()
    if bu:
        return bu.business.id
    
    # Fallback para SuperAdmins o dueños que aún usan Membership
    try:
        membership = Membership.objects.filter(user=user, is_active=True).select_related('business').first()
        if membership and membership.business:
            return membership.business.id
    except Exception:
        pass
    return None


# =============================================================================
# ✅ 1. GESTIÓN DE ROLES
# =============================================================================
class BusinessRoleViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessRoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        business_id = get_user_business_id(self.request.user)
        if business_id:
            return BusinessRole.objects.filter(business_id=business_id)
        return BusinessRole.objects.none()

    def perform_create(self, serializer):
        business_id = get_user_business_id(self.request.user)
        if not business_id:
            raise permissions.PermissionDenied("No se pudo determinar tu negocio.")
        from apps.business.models import Business
        business = Business.objects.get(id=business_id)
        serializer.save(business=business)

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Listar usuarios que tienen este rol activo"""
        role = self.get_object()
        assignments = role.user_assignments.filter(is_active=True).select_related('business_user__user')
        data = [
            {
                "id": str(a.business_user.user.id), 
                "email": a.business_user.user.email, 
                "name": f"{a.business_user.user.first_name} {a.business_user.user.last_name}".strip()
            } 
            for a in assignments
        ]
        return Response(data)


# =============================================================================
# ✅ 2. GESTIÓN DE PERMISOS (Solo lectura)
# =============================================================================
class BusinessPermissionListView(viewsets.ReadOnlyModelViewSet):
    queryset = BusinessPermission.objects.all()
    serializer_class = BusinessPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'name', 'module']
    ordering_fields = ['module', 'code']
    ordering = ['module', 'code']


# =============================================================================
# ✅ 3. GESTIÓN DE USUARIOS DEL NEGOCIO
# =============================================================================
class BusinessUserViewSet(viewsets.ModelViewSet):
    """
    CRUD de usuarios en el contexto del negocio.
    - Crea CustomUser + Membership + BusinessUser + Rol inicial
    - Asigna/Revoca roles con auditoría
    """
    serializer_class = BusinessUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__email', 'user__first_name', 'employee_code']
    lookup_field = 'id'

    def get_queryset(self):
        business_id = get_user_business_id(self.request.user)
        if business_id:
            return BusinessUser.objects.filter(
                business_id=business_id
            ).select_related('user', 'business').prefetch_related('role_assignments__role')
        return BusinessUser.objects.none()

    def create(self, request, *args, **kwargs):
        """Crear usuario del negocio completo"""
        admin_user = request.user
        business_id = get_user_business_id(admin_user)
        
        if not business_id:
            return Response({'error': 'No tienes un negocio activo'}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            email = request.data.get('email')
            if not email:
                return Response({'error': 'Email es requerido'}, status=status.HTTP_400_BAD_REQUEST)
            
            custom_user = User.objects.filter(email=email).first()
            
            if not custom_user:
                serializer = RegisterSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                custom_user = serializer.save()
            else:
                if BusinessUser.objects.filter(user=custom_user, business_id=business_id).exists():
                    return Response({'error': 'Usuario ya pertenece a este negocio'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Sincronizar Membership para compatibilidad con Login/Token
            Membership.objects.get_or_create(
                user=custom_user,
                business_id=business_id,
                defaults={'role': 'USER', 'is_active': True}
            )
            
            # Crear registro BusinessUser
            business_user_data = {
                'user': custom_user,
                'business_id': business_id,
                'employee_code': request.data.get('employee_code'),
                'department': request.data.get('department'),
                'position': request.data.get('position'),
                'hire_date': request.data.get('hire_date'),
            }
            bu_serializer = BusinessUserSerializer(data=business_user_data)
            bu_serializer.is_valid(raise_exception=True)
            business_user = bu_serializer.save()
            
            # Asignar rol inicial si se envía
            role_id = request.data.get('initial_role_id')
            if role_id:
                try:
                    role = BusinessRole.objects.get(id=role_id, business_id=business_id)
                    BusinessUserRoleAssignment.objects.create(
                        business_user=business_user,
                        role=role,
                        assigned_by=admin_user,
                        notes=request.data.get('role_notes', '')
                    )
                except BusinessRole.DoesNotExist:
                    pass

        return Response(BusinessUserSerializer(business_user).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        """Asignar rol a un BusinessUser"""
        business_user = self.get_object()
        role_id = request.data.get('role_id')
        business_id = get_user_business_id(request.user)
        
        if not role_id:
            return Response({'error': 'Se requiere role_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            role = BusinessRole.objects.get(id=role_id, business_id=business_id)
            assignment = BusinessUserRoleAssignment.objects.create(
                business_user=business_user,
                role=role,
                assigned_by=request.user,
                notes=request.data.get('notes', '')
            )
            return Response(BusinessUserRoleAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)
        except BusinessRole.DoesNotExist:
            return Response({'error': 'Rol no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def revoke_role(self, request, pk=None):
        """Revocar rol de un BusinessUser"""
        business_user = self.get_object()
        role_id = request.data.get('role_id')
        
        try:
            assignment = BusinessUserRoleAssignment.objects.get(
                business_user=business_user,
                role_id=role_id,
                is_active=True
            )
            assignment.revoke()
            return Response({'message': 'Rol revocado correctamente'}, status=status.HTTP_200_OK)
        except BusinessUserRoleAssignment.DoesNotExist:
            return Response({'error': 'Asignación no encontrada'}, status=status.HTTP_404_NOT_FOUND)


# =============================================================================
# ✅ 4. HISTÓRICO DE ASIGNACIONES (Solo lectura)
# =============================================================================
class BusinessUserRoleAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BusinessUserRoleAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        business_id = get_user_business_id(self.request.user)
        if business_id:
            return BusinessUserRoleAssignment.objects.filter(
                business_user__business_id=business_id
            ).select_related('business_user__user', 'role', 'assigned_by')
        return BusinessUserRoleAssignment.objects.none()