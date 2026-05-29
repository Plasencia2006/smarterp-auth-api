from rest_framework import permissions

class HasBusinessPermission(permissions.BasePermission):
    """
    Verifica si el usuario tiene un permiso específico en SU negocio.
    Uso en Views: permission_classes = [HasBusinessPermission]
                  required_permission = 'sales.create'
    """
    required_permission = None

    def has_permission(self, request, view):
        if not self.required_permission:
            return True
            
        user = request.user
        if not user.is_authenticated or not hasattr(user, 'business'):
            return False
            
        # Verifica si ALGUNO de sus roles en SU negocio tiene el permiso
        return user.business_roles.filter(
            business=user.business,
            permissions__code=self.required_permission
        ).exists()