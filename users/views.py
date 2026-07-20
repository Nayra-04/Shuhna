from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import User,OTP
from django.core.mail import send_mail
from django.conf import settings as django_settings
from rest_framework.throttling import ScopedRateThrottle

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)

from .serializers import (
    MerchantRegisterSerializer,
    RepRegisterSerializer,
    LoginSerializer,
    LogoutSerializer,
    ChangePasswordSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
    PasswordResetConfirmSerializer,
    VerifyEmailSerializer,
)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


@extend_schema(tags=["Authentication"])
class MerchantRegisterView(generics.CreateAPIView):
    serializer_class = MerchantRegisterSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register Merchant",
        description="Create a new merchant account and return JWT tokens.",
        request=MerchantRegisterSerializer,
        responses={
            201: OpenApiResponse(description="Merchant registered successfully."),
            400: OpenApiResponse(description="Invalid request data."),
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "detail": "تم إنشاء الحساب، تم إرسال كود التأكيد إلى بريدك الإلكتروني",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Authentication"])
class RepRegisterView(generics.CreateAPIView):
    serializer_class = RepRegisterSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register Delivery Representative",
        description="Create a new delivery representative account and return JWT tokens.",
        request=RepRegisterSerializer,
        responses={
            201: OpenApiResponse(description="Representative registered successfully."),
            400: OpenApiResponse(description="Invalid request data."),
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "detail": "تم إنشاء الحساب، تم إرسال كود التأكيد إلى بريدك الإلكتروني",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Authentication"])
class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        description="Authenticate a user and return JWT access and refresh tokens.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="Login successful."),
            400: OpenApiResponse(description="Invalid email or password."),
        },
    )
    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        tokens = get_tokens_for_user(user)

        return Response(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                },
                **tokens,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Authentication"])
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(description="Logout successful."),
            400: OpenApiResponse(description="Invalid refresh token."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
        },
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )
    


@extend_schema(
    tags=["Authentication"],
    description="Generate a new access token using a valid refresh token.",
)
class CustomTokenRefreshView(TokenRefreshView):
    pass

def get_user_with_profile(user_id):
    return User.objects.select_related("merchant_profile", "rep_profile").get(pk=user_id)

class ProfileRetrieveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["User Profile"],responses=ProfileSerializer)
    def get(self, request):
        user = get_user_with_profile(request.user.id)
        serializer = ProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=["User Profile"],
        request={"multipart/form-data": ProfileUpdateSerializer},
        responses=ProfileSerializer,
    )
    def patch(self, request):
        user = get_user_with_profile(request.user.id)

        serializer = ProfileUpdateSerializer(
            instance=user, data=request.data, partial=True  
        )
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        output = ProfileSerializer(updated_user)
        return Response(output.data, status=status.HTTP_200_OK)


class ProfileDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["User Profile"],responses=None)
    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(
            {"detail": "تم تعطيل الحساب بنجاح"},
            status=status.HTTP_200_OK,
        )

@extend_schema(tags=["Authentication"])
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer, responses=None)
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        if not user.check_password(old_password):
            return Response(
                {"detail": "كلمة المرور الحالية غير صحيحة"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if old_password == new_password:
            return Response(
                {"detail": "كلمة المرور الجديدة يجب أن تختلف عن الحالية"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response(
            {"detail": "تم تغيير كلمة المرور بنجاح"},
            status=status.HTTP_200_OK,
        )
    

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset_request"

    @extend_schema(
        tags=["Authentication"],
        description=(
            "Send a one-time verification code to the user's email address "
        ),
        request=PasswordResetRequestSerializer,
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email__iexact=email).first()

        generic_response = {
            "detail": "إذا كان البريد الإلكتروني مسجلًا لدينا، فسيتم إرسال رمز التحقق إليه."
        }

        if user is not None:
            otp = OTP.generate_for_user(user)
            send_mail(
            subject="إعادة تعيين كلمة المرور لتطبيق شحنة",
                message=(
                    f"مرحبًا،\n\n"
                    f"لقد تلقينا طلبًا لإعادة تعيين كلمة المرور الخاصة بحسابك.\n\n"
                    f"رمز التحقق الخاص بك هو:\n\n"
                    f"{otp.code}\n\n"
                    f"هذا الرمز صالح لمدة 10 دقائق.\n"
                    f"إذا لم تطلب إعادة تعيين كلمة المرور، يمكنك تجاهل هذه الرسالة.\n\n"
                    f"مع تحيات فريق شحنة."
                ),
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

        return Response(generic_response, status=status.HTTP_200_OK)


class PasswordResetVerifyView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset_verify"

    @extend_schema(
            tags=["Authentication"],
            request=PasswordResetVerifySerializer, 
            description="Verify the one-time password (OTP) sent to the user's email.",
            responses=None
    )
    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {"detail": "تم التحقق من الرمز بنجاح. يمكنك الآن تعيين كلمة مرور جديدة."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
            tags=["Authentication"],
            description=("Reset the user's password using the verified OTP code."),
            request=PasswordResetConfirmSerializer,
            responses=None
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        otp = serializer.validated_data["otp"]
        new_password = serializer.validated_data["new_password"]

        user.set_password(new_password)
        user.save(update_fields=["password"])

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        return Response(
            {"detail": "تم تغيير كلمة المرور بنجاح"},
            status=status.HTTP_200_OK,
        )
    
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset_verify"

    @extend_schema(
        tags=["Authentication"],
        description=(
            "Send a one-time verification code to the user's email address "
        ),
        request=VerifyEmailSerializer,
        responses=None
    )
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        otp = serializer.validated_data["otp"]

        user.is_active = True
        user.save(update_fields=["is_active"])

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        tokens = get_tokens_for_user(user)
        return Response(
            {
                "detail": "تم تأكيد الحساب بنجاح",
                "user": {"id": user.id, "email": user.email, "role": user.role},
                **tokens,
            },
            status=status.HTTP_200_OK,
        )
    
class ResendVerificationCodeView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset_request"

    @extend_schema(
        tags=["Authentication"],
        description=(
            "Resend a one-time verification code to the user's email address "
        ),
        request=VerifyEmailSerializer,
        responses=None
    )
    def post(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email__iexact=email, is_active=False).first()

        if user is not None:
            otp = OTP.generate_for_user(user, purpose=OTP.Purpose.EMAIL_VERIFICATION)
            send_mail(
                subject="تأكيد حسابك في شحنة",
                message=(
                    f"مرحبًا،\n\n"
                    f"شكرًا لتسجيلك في شحنة.\n\n"
                    f"رمز تأكيد الحساب الخاص بك هو:\n\n"
                    f"{otp.code}\n\n"
                    f"هذا الرمز صالح لمدة 10 دقائق.\n"
                    f"يرجى عدم مشاركة هذا الرمز مع أي شخص حفاظًا على أمان حسابك.\n\n"
                    f"إذا لم تقم بإنشاء هذا الحساب، يمكنك تجاهل هذه الرسالة.\n\n"
                    f"مع تحيات،\n"
                    f"فريق شحنة"
                ),
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

        return Response(
            {"detail": "إذا كان الحساب غير مفعل، تم إرسال كود جديد"},
            status=status.HTTP_200_OK,
        )