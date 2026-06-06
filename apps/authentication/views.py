from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

from .serializers import (
    RegisterSerializer, 
    UserDetailSerializer, 
    CustomTokenObtainPairSerializer,
    UserSerializer,  # ← Solo una vez
)
from .permissions import IsSuperAdmin  # ← Solo una vez

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Registro de nuevos usuarios (público)"""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response(
            {
                'message': 'Usuario registrado exitosamente.',
                'user': {
                    'id': str(user.id), 
                    'email': user.email, 
                    'username': user.username
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """Login con JWT - devuelve tokens + datos del usuario"""
    serializer_class = CustomTokenObtainPairSerializer


class MeView(generics.RetrieveAPIView):
    """Obtener perfil del usuario actual + memberships"""
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class LoginView(TokenObtainPairView):
    """Login con JWT - devuelve tokens + datos del usuario"""
    serializer_class = CustomTokenObtainPairSerializer


class MeView(generics.RetrieveAPIView):
    """Obtener perfil del usuario actual + memberships"""
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UserListView(generics.ListCreateAPIView):
    """
    Lista y crea usuarios del sistema - SOLO Super Admin
    GET /auth/users/  → Listar (Super Admins + Usuarios sin negocio)
    POST /auth/users/ → Crear
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    # ✅ AGREGAR: serializer_class por defecto (para GET)
    serializer_class = UserSerializer
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'is_active', 'is_superuser']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'username', 'email', 'estado']
    ordering = ['-date_joined']
    
    # ✅ AGREGAR: Método para cambiar serializer según la acción
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RegisterSerializer  # Para creación con password
        return UserSerializer  # Para lectura/lista
    
    def get_queryset(self):
        """
        Solo Super Admins y usuarios SIN negocio asignado.
        Los usuarios del negocio están en business_roles_businessuser.
        """
        from apps.business_roles.models import BusinessUser
        
        # ✅ Filtrar: Super Admins O usuarios que NO son BusinessUser
        queryset = User.objects.filter(
            Q(is_superuser=True) | 
            Q(is_super_admin=True) |
            ~Q(id__in=BusinessUser.objects.values_list('user_id', flat=True))
        ).distinct()
        
        # Búsqueda
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Crear usuario del sistema (sin negocio asignado)"""
        print(f"🔍 [CREATE] Request data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        print(f"✅ Usuario creado: {user.id} - {user.email}")
        
        # Retornar con UserSerializer para incluir business_memberships
        read_serializer = UserSerializer(user, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'results': serializer.data,
            'count': queryset.count(),
            'next': None,
            'previous': None,
        })


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """CRUD completo de usuario - SOLO Super Admin"""
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer  # Por defecto para GET
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    lookup_field = 'id'
    
    # ✅ CORREGIDO: Usar request.method en lugar de self.action
    def get_serializer_class(self):
        """Usar UserUpdateSerializer para actualizaciones"""
        if self.request.method in ['PUT', 'PATCH']:
            from .serializers import UserUpdateSerializer
            return UserUpdateSerializer
        return UserDetailSerializer
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Retornar con UserSerializer para incluir business_memberships
        return Response({
            'message': 'Usuario actualizado exitosamente.',
            'user': UserSerializer(serializer.instance, context={'request': request}).data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Soft delete: cambiar estado en lugar de eliminar
        if hasattr(instance, 'estado'):
            instance.estado = 'ELIMINADO'
            instance.save(update_fields=['estado'])
            return Response({'message': 'Usuario eliminado exitosamente.'})
        
        self.perform_destroy(instance)
        return Response({'message': 'Usuario eliminado exitosamente.'})

# ✅ AGREGAR: Vista para CREAR usuarios (POST /auth/users/)
# =============================================================================
class UserCreateView(generics.CreateAPIView):
    """
    Crear nuevo usuario - SOLO Super Admin
    POST /auth/users/
    """
    serializer_class = RegisterSerializer  # Usa el serializer de registro con password
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def create(self, request, *args, **kwargs):
        print(f"🔍 [UserCreateView] Creating user with data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Retornar con UserSerializer para incluir business_memberships
        read_serializer = UserSerializer(user, context={'request': request})
        
        print(f"✅ User created: {user.id} - {user.email}")
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)