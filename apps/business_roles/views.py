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

# apps/business_roles/views.py

    def create(self, request, *args, **kwargs):
        """
        Crear usuario del negocio.
        """
        admin_user = request.user
        business_id = get_user_business_id(admin_user)
        
        if not business_id:
            return Response({
                'error': 'No se pudo determinar el negocio'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email = request.data.get('email')
        
        # ✅ OBTENER EL ROL DEL REQUEST (CAJERO, VENDEDOR, CONTADOR, etc.)
        # Puede venir como 'role' o 'initial_role_id' o 'membership_role'
        membership_role = (
            request.data.get('membership_role') or 
            request.data.get('role') or 
            'USER'  # Solo si no se especifica
        )
        
        print(f"🔍 [CREATE] Membership role recibido: {membership_role}")
        print(f"🔍 [CREATE] Request data completo: {request.data}")
        
        with transaction.atomic():
            # 1. Buscar o crear CustomUser
            custom_user = User.objects.filter(email=email).first()
            
            if not custom_user:
                custom_user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=request.data.get('password', 'temp_password_123'),
                    first_name=request.data.get('first_name', ''),
                    last_name=request.data.get('last_name', ''),
                    is_active=True
                )
            
            # 2. Verificar si ya es BusinessUser
            if BusinessUser.objects.filter(user=custom_user, business_id=business_id).exists():
                return Response({
                    'error': 'El usuario ya pertenece a este negocio'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 3. Crear BusinessUser
            business_user = BusinessUser.objects.create(
                user=custom_user,
                business_id=business_id,
                employee_code=request.data.get('employee_code'),
                department=request.data.get('department'),
                position=request.data.get('position'),
                hire_date=request.data.get('hire_date'),
                is_active=True
            )
            
            # ✅ 4. CREAR MEMBERSHIP CON EL ROL CORRECTO
            from apps.business.models import Membership
            
            membership, created = Membership.objects.get_or_create(
                user=custom_user,
                business_id=business_id,
                defaults={
                    'role': membership_role.upper(),  # ← CAJERO, VENDEDOR, etc.
                    'is_active': True
                }
            )
            
            if not created:
                membership.role = membership_role.upper()
                membership.is_active = True
                membership.save()
            
            print(f"✅ [CREATE] Membership creada con role: {membership.role}")
            
            # 5. Asignar rol inicial si se especifica
            role_id = request.data.get('initial_role_id')
            if role_id:
                try:
                    role_obj = BusinessRole.objects.get(id=role_id, business_id=business_id)
                    BusinessUserRoleAssignment.objects.create(
                        business_user=business_user,
                        role=role_obj,
                        assigned_by=admin_user,
                        notes=request.data.get('role_notes', '')
                    )
                except BusinessRole.DoesNotExist:
                    pass
        
        serializer = self.get_serializer(business_user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """
        Actualizar BusinessUser + CustomUser relacionado.
        Maneja campos del BusinessUser, CustomUser y contraseña.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        print(f"\n{'='*80}")
        print(f"🔍 [UPDATE] BusinessUser ID: {instance.id}")
        print(f"🔍 [UPDATE] CustomUser ID: {instance.user.id}")
        print(f"🔍 [UPDATE] Request data: {request.data}")
        print(f"{'='*80}\n")
        
        # ✅ PASO 1: Extraer y actualizar campos del CustomUser
        user = instance.user
        user_updated = False
        
        # first_name
        first_name = request.data.get('first_name')
        if first_name is not None and first_name != user.first_name:
            user.first_name = first_name
            user_updated = True
            print(f"✅ [UPDATE] first_name actualizado: {first_name}")
        
        # last_name
        last_name = request.data.get('last_name')
        if last_name is not None and last_name != user.last_name:
            user.last_name = last_name
            user_updated = True
            print(f"✅ [UPDATE] last_name actualizado: {last_name}")
        
        # email
        email = request.data.get('email')
        if email is not None and email != user.email:
            from apps.authentication.models import CustomUser
            if CustomUser.objects.filter(email=email).exclude(id=user.id).exists():
                return Response({
                    'error': 'Este email ya está en uso por otro usuario',
                    'detail': {'email': ['Este email ya está registrado']}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.email = email
            user.username = email
            user_updated = True
            print(f"✅ [UPDATE] email actualizado: {email}")
        
        # ✅ PASO 2: Actualizar contraseña si se proporcionó
        password = request.data.get('password')
        if password and password.strip():
            user.set_password(password)  # ← Hashea la contraseña
            user_updated = True
            print(f"✅ [UPDATE] Contraseña actualizada (hasheada)")
        
        # Guardar cambios del CustomUser
        if user_updated:
            user.save()
            print(f"✅ [UPDATE] CustomUser guardado: {user.id}")
        
        # ✅ PASO 3: Actualizar campos del BusinessUser
        business_data = request.data.copy()
        business_data.pop('first_name', None)
        business_data.pop('last_name', None)
        business_data.pop('email', None)
        business_data.pop('password', None)
        business_data.pop('password_confirm', None)
        
        serializer = self.get_serializer(instance, data=business_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        print(f"✅ [UPDATE] Serializer validado: {serializer.validated_data}")
        
        self.perform_update(serializer)
        
        # ✅ PASO 4: Retornar respuesta
        instance.refresh_from_db()
        response_serializer = self.get_serializer(instance)
        
        print(f"✅ [UPDATE] Respuesta lista")
        print(f"{'='*80}\n")
        
        return Response(response_serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """PATCH - usa la misma lógica que update"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


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