from django.urls import path
from .views import BusinessCreateListView, MembershipAssignView, MembershipListView

urlpatterns = [
    path('', BusinessCreateListView.as_view(), name='business-list-create'),
    path('membership/', MembershipListView.as_view(), name='membership-list'),
    path('membership/assign/', MembershipAssignView.as_view(), name='membership-assign'),
]