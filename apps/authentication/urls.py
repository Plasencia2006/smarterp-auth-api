from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterView, 
    LoginView, 
    MeView, 
    UserListView,
    UserDetailView,
    UserCreateView,
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
    
    # ✅ AGREGAR: Ruta para crear usuarios (POST)
    path('users/', UserCreateView.as_view(), name='user-create'),  # ← POST
    # ✅ UserListView ahora soporta GET y POST en la misma URL
    path('users/', UserListView.as_view(), name='user-list-create'),
    
    # Ruta existente para listar usuarios (GET)
    path('users/', UserListView.as_view(), name='user-list'),  # ← GET
    # Incluir router si se usa
    # path('', include(router.urls)),
    
]