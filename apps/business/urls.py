# apps/business/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusinessViewSet, MembershipViewSet

router = DefaultRouter()
router.register(r'', BusinessViewSet, basename='business')
router.register(r'memberships', MembershipViewSet, basename='membership')

urlpatterns = [
    path('', include(router.urls)),
]