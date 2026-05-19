from django.urls import path
from .views import UserListView
from .views import UserListView, UserDetailView, UserHistoryView

urlpatterns = [
    # Lista de usuarios (Super Admin only)
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<uuid:id>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<uuid:id>/history/', UserHistoryView.as_view(), name='user-history'),
]