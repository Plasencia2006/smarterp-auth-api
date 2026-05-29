# apps/business/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusinessViewSet, MembershipViewSet, BusinessUserViewSet

router = DefaultRouter()

# ✅ CAMBIO CLAVE: Registrar con prefijo 'businesses'
router.register(r'businesses', BusinessViewSet, basename='business')
router.register(r'memberships', MembershipViewSet, basename='membership')
router.register(r'users', BusinessUserViewSet, basename='business-user')

urlpatterns = [
    path('', include(router.urls)),
]