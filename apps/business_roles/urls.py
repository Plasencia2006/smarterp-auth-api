from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusinessRoleViewSet, BusinessPermissionListView

router = DefaultRouter()
router.register(r'roles', BusinessRoleViewSet, basename='business-role')
router.register(r'permissions', BusinessPermissionListView, basename='business-permission')

urlpatterns = [
    path('', include(router.urls)),
]