from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BusinessRoleViewSet, 
    BusinessPermissionListView, 
    BusinessUserViewSet, 
    BusinessUserRoleAssignmentViewSet
)

router = DefaultRouter()
router.register(r'roles', BusinessRoleViewSet, basename='business-role')
router.register(r'permissions', BusinessPermissionListView, basename='business-permission')
router.register(r'users', BusinessUserViewSet, basename='business-user')
router.register(r'role-assignments', BusinessUserRoleAssignmentViewSet, basename='role-assignment')

urlpatterns = [
    path('', include(router.urls)),
]