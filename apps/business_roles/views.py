from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import BusinessPermission, BusinessRole
from .serializers import BusinessPermissionSerializer, BusinessRoleSerializer

def get_user_business_id(user):
    """Obtiene el business_id del usuario vía FK directa o Membership"""
    if hasattr(user, 'business') and user.business:
        return user.business.id
    try:
        from apps.business.models import Membership
        membership = Membership.objects.filter(user=user, is_active=True).select_related('business').first()
        if membership and membership.business:
            return membership.business.id
    except Exception:
        pass
    return None

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
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No se pudo determinar tu negocio para crear el rol.")
        from apps.business.models import Business
        business = Business.objects.get(id=business_id)
        serializer.save(business=business)

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        role = self.get_object()
        users = role.users.all()
        data = [{"id": str(u.id), "email": u.email, "name": f"{u.first_name} {u.last_name}".strip()} for u in users]
        return Response(data)

class BusinessPermissionListView(viewsets.ReadOnlyModelViewSet):
    queryset = BusinessPermission.objects.all()
    serializer_class = BusinessPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'name', 'module']
    ordering_fields = ['module', 'code']
    ordering = ['module', 'code']