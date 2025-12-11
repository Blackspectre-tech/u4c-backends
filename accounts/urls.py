from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    CustomTokenObtainPairView,
    RegisterUserView,
    RegisterOrganizationView,
    AccountActivationView,
    UserResendActivationView,
    UserPasswordResetView,
    UserConfirmPasswordResetView,
    UpdateProfileView,
    UpdateOrganizationView,
    UploadAvatarView,
    RetrieveOrganization,
    AddWalletView,
    TransactionListView,
    ProfileView,
    OrganizationKYC,
    TipTreasuryCreateView,
)

urlpatterns = [
    # path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register-user/', RegisterUserView.as_view()),
    path('register-organization/', RegisterOrganizationView.as_view()),
    path('organization/kyc/', OrganizationKYC.as_view()),
    path('activate/', AccountActivationView.as_view()),
    path('resend-activation-otp/', UserResendActivationView.as_view()),
    path('password-reset/', UserPasswordResetView.as_view()),
    path('confirm-password-reset/', UserConfirmPasswordResetView.as_view()),
    path('update-userprofile/', UpdateProfileView.as_view()),
    path('update-organization/', UpdateOrganizationView.as_view()),
    path('organization/<uuid:pk>/', RetrieveOrganization.as_view()),
    path('upload-avatar/',UploadAvatarView.as_view()),
    path('add-wallet/',AddWalletView.as_view()),
    path('my-profile/',ProfileView.as_view()),
    path('transactions/',TransactionListView.as_view()),
    path('transactions/add/',TipTreasuryCreateView.as_view()),
]
