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
    """Registro de nuevos usuarios"""
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


class UserListView(generics.ListAPIView):
    """
    Lista todos los usuarios del sistema - SOLO Super Admin
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'is_active', 'is_superuser']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'username', 'email', 'estado']
    ordering = ['-date_joined']
    
    def get_queryset(self):
        # ✅ CORREGIDO: QuerySet simple sin relaciones que puedan no existir
        queryset = User.objects.all()
        
        # ✅ Búsqueda personalizada
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # ✅ Filtro por estado
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado__iexact=estado)
        
        return queryset
    
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
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    lookup_field = 'id'
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Usuario actualizado exitosamente.',
            'user': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # ✅ Soft delete: cambiar estado en lugar de eliminar
        if hasattr(instance, 'estado'):
            instance.estado = 'ELIMINADO'
            instance.save(update_fields=['estado'])
            return Response({'message': 'Usuario eliminado exitosamente.'})
        
        self.perform_destroy(instance)
        return Response({'message': 'Usuario eliminado exitosamente.'})