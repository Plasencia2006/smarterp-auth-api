from rest_framework.permissions import BasePermission
from apps.business.models import Membership


class IsSuperAdmin(BasePermission):
    message = 'Se requiere ser Super Admin.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_super_admin)


class IsBusinessAdmin(BasePermission):
    message = 'Debes ser Administrador de este negocio.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_super_admin:
            return True
        business = getattr(request, 'business', None)
        if not business:
            return False
        return Membership.objects.filter(
            user=request.user, business=business,
            role=Membership.Role.ADMIN, is_active=True,
        ).exists()


class IsVendedor(BasePermission):
    message = 'Se requiere rol de Vendedor o superior.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_super_admin:
            return True
        business = getattr(request, 'business', None)
        if not business:
            return False
        return Membership.objects.filter(
            user=request.user, business=business,
            role__in=[Membership.Role.ADMIN, Membership.Role.VENDEDOR],
            is_active=True,
        ).exists()


class IsCliente(BasePermission):
    message = 'Debes ser miembro activo de este negocio.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_super_admin:
            return True
        business = getattr(request, 'business', None)
        if not business:
            return False
        return Membership.objects.filter(
            user=request.user, business=business, is_active=True,
        ).exists()


class IsSuperAdminOrBusinessAdmin(BasePermission):
    message = 'Se requiere ser Super Admin o Admin del negocio.'

    def has_permission(self, request, view):
        return (
            IsSuperAdmin().has_permission(request, view)
            or IsBusinessAdmin().has_permission(request, view)
        )