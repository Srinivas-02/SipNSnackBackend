# accounts/urls.py

from django.urls import path

from pos.apps.accounts._views.login import LocationLoginView, UserLoginView
from .views import (
    ChangePasswordView,
    FranchiseAdminView,
    LogoutView,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('login-location/', LocationLoginView.as_view(), name='login'),
    path('login-user/', UserLoginView.as_view(), name='login'),
    path('change-password/', ChangePasswordView.as_view()),
    path('franchise-admin/', FranchiseAdminView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
