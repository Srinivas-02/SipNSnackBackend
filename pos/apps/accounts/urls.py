# accounts/urls.py

from django.urls import path
from .views import (
    ChangePasswordView,
    FranchiseAdminView,
    LoginView,
    LogoutView,
)

urlpatterns = [
    path('login/',LoginView.as_view()),
    path('change-password/', ChangePasswordView.as_view()),
    path('franchise-admin/', FranchiseAdminView.as_view()),
    path('logout/',LogoutView.as_view()),
]
