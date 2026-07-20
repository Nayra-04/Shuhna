from django.urls import path

from .views import (
    MerchantRegisterView,
    RepRegisterView,
    LoginView,
    LogoutView,
    CustomTokenRefreshView,
    ChangePasswordView,
    ProfileRetrieveView,
    ProfileUpdateView,
    ProfileDeleteView,
    PasswordResetRequestView,
    PasswordResetVerifyView,
    PasswordResetConfirmView,
    VerifyEmailView,
    ResendVerificationCodeView,
)

urlpatterns = [
    path("register/merchant/", MerchantRegisterView.as_view(), name="register-merchant"),
    path("register/rep/", RepRegisterView.as_view(), name="register-rep"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token-refresh"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("password-reset/request/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/verify/", PasswordResetVerifyView.as_view(), name="password-reset-verify"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("verify-email/resend/", ResendVerificationCodeView.as_view(), name="verify-email-resend"),
    path("profile/", ProfileRetrieveView.as_view(), name="profile-get"),
    path("profile/update/", ProfileUpdateView.as_view(), name="profile-update"),
    path("profile/delete/", ProfileDeleteView.as_view(), name="profile-delete"),

]