# superadmin/views.py

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Q

# ✅ IMPORTAR LOS SERIALIZERS CORRECTOS
from apps.authentication.serializers import (
    RegisterSerializer, 
    UserSerializer, 
    UserUpdateSerializer  # ← ESTE ES EL QUE FALTABA
)
from .permissions import IsSuperAdmin

User = get_user_model()


class UserListView(generics.ListCreateAPIView):
    """
    Lista usuarios (GET) y crea nuevos (POST).
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def get_queryset(self):
        queryset = User.objects.all().only(
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_superuser', 'is_staff', 'estado', 'is_active',
            'date_joined', 'last_login'
        ).order_by('-date_joined')
        
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | 
                Q(username__icontains=search)
            )
        
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado__iexact=estado)
        
        return queryset

    def get_serializer_class(self):
        """
        ✅ Si es POST (Crear), usa RegisterSerializer (maneja password).
        ✅ Si es GET (Listar), usa UserSerializer (solo lectura).
        """
        if self.request.method == 'POST':
            return RegisterSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        """
        Crea el usuario y retorna respuesta personalizada.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(
            {
                'message': 'Usuario creado exitosamente',
                'user': UserSerializer(serializer.instance).data
            },
            status=status.HTTP_201_CREATED
        )


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Ver, actualizar (PATCH) o eliminar (DELETE) un usuario.
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        return User.objects.all()
    
    def get_serializer_class(self):
        """
        ✅ Usa UserUpdateSerializer para actualizaciones (permite editar)
        ✅ Usa UserSerializer para lectura (GET)
        """
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer  # ← AHORA SÍ ESTÁ DEFINIDO
        return UserSerializer

    def patch(self, request, *args, **kwargs):
        """Actualización parcial"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """
        ✅ Actualiza usuario y retorna respuesta personalizada
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(
            {
                'message': 'Usuario actualizado exitosamente',
                'user': UserSerializer(instance).data
            }
        )

    def delete(self, request, *args, **kwargs):
        """Soft delete: solo desactivar"""
        instance = self.get_object()
        instance.is_active = False
        instance.estado = 'ELIMINADO'
        instance.save(update_fields=['is_active', 'estado'])
        return Response(
            {'detail': 'Usuario eliminado exitosamente.'},
            status=status.HTTP_204_NO_CONTENT
        )


class UserHistoryView(generics.RetrieveAPIView):
    """
    Obtiene el historial de acciones del usuario.
    """
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        return User.objects.all()
    
    def get(self, request, *args, **kwargs):
        user = self.get_object()
        
        # Historial simulado
        mock_history = [
            {
                'action': 'CREACIÓN',
                'description': 'Cuenta creada en el sistema',
                'date': user.date_joined,
                'by': 'System'
            },
            {
                'action': 'MODIFICACIÓN',
                'description': 'Se actualizó el estado a ACTIVO',
                'date': user.last_login or user.date_joined,
                'by': 'Admin'
            },
            {
                'action': 'PERMISOS',
                'description': 'Se otorgaron permisos de Super Admin',
                'date': user.date_joined,
                'by': request.user.username
            }
        ]
        
        return Response({
            'user_id': str(user.id),
            'history': mock_history
        })
        
# superadmin/views.py - dentro de UserDetailView

def update(self, request, *args, **kwargs):
    """
    ✅ Actualiza usuario con logging detallado
    """
    import logging
    logger = logging.getLogger(__name__)
    
    partial = kwargs.pop('partial', False)
    instance = self.get_object()
    
    logger.info(f"🔍 PATCH request para usuario {instance.id}")
    logger.info(f"📦 Datos recibidos: {dict(request.data)}")
    
    serializer = self.get_serializer(instance, data=request.data, partial=partial)
    
    if not serializer.is_valid():
        logger.error(f"❌ Errores de validación: {serializer.errors}")
        
        return Response(
            {
                'success': False,
                'errors': serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    self.perform_update(serializer)
    
    logger.info(f"✅ Usuario {instance.id} actualizado exitosamente")
    
    return Response(
        {
            'success': True,
            'message': 'Usuario actualizado exitosamente',
            'user': UserSerializer(instance).data
        }
    )