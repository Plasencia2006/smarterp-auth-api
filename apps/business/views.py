from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Business, Membership
from .serializers import BusinessSerializer, MembershipSerializer
from apps.authentication.permissions import IsSuperAdminOrBusinessAdmin


class BusinessCreateListView(generics.ListCreateAPIView):
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Business.objects.select_related('owner').all()
        return Business.objects.filter(
            memberships__user=user, memberships__is_active=True
        ).select_related('owner').distinct()


class MembershipAssignView(generics.CreateAPIView):
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrBusinessAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        return Response(
            {'message': f'Usuario asignado con rol {membership.role}.', 'id': str(membership.id)},
            status=status.HTTP_201_CREATED,
        )


class MembershipListView(generics.ListAPIView):
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrBusinessAdmin]

    def get_queryset(self):
        business = getattr(self.request, 'business', None)
        if not business:
            return Membership.objects.none()
        return Membership.objects.filter(business=business).select_related('user', 'business')