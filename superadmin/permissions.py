from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """
    Permite acceso solo a usuarios Super Admin.
    Soporta tanto el campo personalizado `is_super_admin` como el nativo `is_superuser` de Django.
    """
    message = 'Se requiere ser Super Admin para realizar esta acción.'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Verificar ambos campos para máxima compatibilidad
        return bool(
            getattr(request.user, 'is_super_admin', False) or 
            request.user.is_superuser
        )


class IsBusinessAdmin(BasePermission):
    """Permite acceso a administradores de un negocio específico"""
    message = 'Debes ser Administrador de este negocio.'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super Admin tiene acceso universal
        if getattr(request.user, 'is_super_admin', False) or request.user.is_superuser:
            return True
        
        # Verificar membresía como ADMIN
        try:
            from apps.business.models import Membership
            business = getattr(request, 'business', None)
            if not business:
                return False
            
            return Membership.objects.filter(
                user=request.user, 
                business=business,
                role=Membership.Role.ADMIN, 
                is_active=True,
            ).exists()
        except ImportError:
            return False


class IsVendedor(BasePermission):
    """Permite acceso a vendedores y roles superiores"""
    message = 'Se requiere rol de Vendedor o superior.'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if getattr(request.user, 'is_super_admin', False) or request.user.is_superuser:
            return True
        
        try:
            from apps.business.models import Membership
            business = getattr(request, 'business', None)
            if not business:
                return False
            
            return Membership.objects.filter(
                user=request.user, 
                business=business,
                role__in=[Membership.Role.ADMIN, Membership.Role.VENDEDOR],
                is_active=True,
            ).exists()
        except ImportError:
            return False


class IsCliente(BasePermission):
    """Permite acceso a cualquier miembro activo del negocio"""
    message = 'Debes ser miembro activo de este negocio.'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if getattr(request.user, 'is_super_admin', False) or request.user.is_superuser:
            return True
        
        try:
            from apps.business.models import Membership
            business = getattr(request, 'business', None)
            if not business:
                return False
            
            return Membership.objects.filter(
                user=request.user, 
                business=business, 
                is_active=True,
            ).exists()
        except ImportError:
            return False


class IsSuperAdminOrBusinessAdmin(BasePermission):
    """Permite acceso a Super Admin O Admin del negocio actual"""
    message = 'Se requiere ser Super Admin o Admin del negocio.'
    
    def has_permission(self, request, view):
        return (
            IsSuperAdmin().has_permission(request, view) or
            IsBusinessAdmin().has_permission(request, view)
        )