from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterView, 
    LoginView, 
    MeView, 
    UserListView,
    UserDetailView
)

# ✅ Router para endpoints RESTful (opcional, si quieres usar ViewSet)
router = DefaultRouter()
# router.register(r'users', UserViewSet, basename='user')  # Si usas ViewSet

urlpatterns = [
    # Auth endpoints
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('me/', MeView.as_view(), name='auth-me'),
    
    # User management (Super Admin only)
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<uuid:id>/', UserDetailView.as_view(), name='user-detail'),
    
    # Incluir router si se usa
    # path('', include(router.urls)),
]