from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, MerchantProfile, RepProfile, OTP
import re
from .validators import validate_strong_password
from django.core.mail import send_mail
from django.conf import settings as django_settings
from django.contrib.gis.geos import Point
from django.utils import timezone


class BaseRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    full_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("البريد الإلكتروني مستخدم بالفعل")
        return value

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("رقم الهاتف مستخدم بالفعل")
        return value

    def validate_password(self, value):
        return validate_strong_password(value)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "كلمة المرور وتأكيدها غير متطابقين"}
            )
        return attrs


class MerchantRegisterSerializer(BaseRegisterSerializer):
    shop_name = serializers.CharField(max_length=150)
    shop_address = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        shop_name = validated_data.pop("shop_name")
        shop_address = validated_data.pop("shop_address", "")

        with transaction.atomic():
            user = User.objects.create_user(
                email=validated_data["email"],
                phone=validated_data["phone"],
                full_name=validated_data["full_name"],
                password=validated_data["password"],
                role=User.Role.MERCHANT,
                is_active=False, 
            )
            MerchantProfile.objects.create(
                user=user, shop_name=shop_name, shop_address=shop_address
            )

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
        return user


class RepRegisterSerializer(BaseRegisterSerializer):
    vehicle_type = serializers.ChoiceField(choices=RepProfile.VehicleType.choices)

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        vehicle_type = validated_data.pop("vehicle_type")

        with transaction.atomic():
            user = User.objects.create_user(
                email=validated_data["email"],
                phone=validated_data["phone"],
                full_name=validated_data["full_name"],
                password=validated_data["password"],
                role=User.Role.REP,
                is_active=False, 
            )
            RepProfile.objects.create(user=user, vehicle_type=vehicle_type)

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
        return user



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"]
        password = attrs["password"]

        user = User.objects.filter(email__iexact=email).first()

        if user is None:
            raise serializers.ValidationError("البريد الإلكتروني أو كلمة المرور غير صحيحة")

        if not user.check_password(password):
            raise serializers.ValidationError("البريد الإلكتروني أو كلمة المرور غير صحيحة")

        if not user.is_active:
            raise serializers.ValidationError(
                "الحساب غير مفعل، يرجى تأكيد بريدك الإلكتروني أولاً"
            )

        attrs["user"] = user
        return attrs



class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate_refresh(self, value):
        try:
            self.token = RefreshToken(value)
        except Exception:
            raise serializers.ValidationError("رمز تسجيل الخروج غير صالح.")
        return value

    def save(self, **kwargs):
        self.token.blacklist()



class MerchantProfileNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantProfile
        fields = ["shop_name", "shop_address", "shop_location"]


class RepProfileNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepProfile
        fields = ["vehicle_type", "current_location"]


class ProfileSerializer(serializers.ModelSerializer):
    merchant_profile = MerchantProfileNestedSerializer(read_only=True)
    rep_profile = RepProfileNestedSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "phone", "full_name", "image", "role",
            "merchant_profile", "rep_profile",
        ]
        read_only_fields = fields  

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.role == User.Role.MERCHANT:
            data.pop("rep_profile", None)
        else:
            data.pop("merchant_profile", None)
        return data



class ProfileUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=False, max_length=150)
    image = serializers.ImageField(required=False)

    shop_name = serializers.CharField(required=False, max_length=150)
    shop_address = serializers.CharField(required=False, allow_blank=True, max_length=255)
    shop_lat = serializers.FloatField(required=False, write_only=True)
    shop_lng = serializers.FloatField(required=False, write_only=True)

    vehicle_type = serializers.ChoiceField(
        choices=RepProfile.VehicleType.choices, required=False
    )
    current_lat = serializers.FloatField(required=False, write_only=True)
    current_lng = serializers.FloatField(required=False, write_only=True)

    def update(self, instance, validated_data):
        if "full_name" in validated_data:
            instance.full_name = validated_data["full_name"]
        if "image" in validated_data:
            instance.image = validated_data["image"]
        instance.save()

        if instance.role == User.Role.MERCHANT and hasattr(instance, "merchant_profile"):
            profile = instance.merchant_profile
            if "shop_name" in validated_data:
                profile.shop_name = validated_data["shop_name"]
            if "shop_address" in validated_data:
                profile.shop_address = validated_data["shop_address"]
            if "shop_lat" in validated_data and "shop_lng" in validated_data:
                profile.shop_location = Point(
                    validated_data["shop_lng"], validated_data["shop_lat"], srid=4326
                )
            profile.save()

        elif instance.role == User.Role.REP and hasattr(instance, "rep_profile"):
            profile = instance.rep_profile
            if "vehicle_type" in validated_data:
                profile.vehicle_type = validated_data["vehicle_type"]
            if "current_lat" in validated_data and "current_lng" in validated_data:
                profile.current_location = Point(
                    validated_data["current_lng"], validated_data["current_lat"], srid=4326
                )
                profile.last_location_update = timezone.now()
            profile.save()

        return instance
    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        return validate_strong_password(value)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return attrs
    

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value


class PasswordResetVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(email__iexact=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "البريد الإلكتروني أو رمز التحقق غير صحيح."}
            )

        otp = (
            OTP.objects.filter(user=user, code=attrs["code"])
            .order_by("-created_at")
            .first()
        )

        if otp is None or not otp.is_valid():
            raise serializers.ValidationError(
                {"code": "رمز التحقق غير صحيح أو انتهت صلاحيته."}
            )

        attrs["user"] = user
        attrs["otp"] = otp
        return attrs


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        return validate_strong_password(value)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {
                    "confirm_password": "كلمة المرور الجديدة وتأكيد كلمة المرور غير متطابقين."
                }
            )

        try:
            user = User.objects.get(email__iexact=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "البريد الإلكتروني أو رمز التحقق غير صحيح."}
            )

        otp = (
            OTP.objects.filter(user=user, code=attrs["code"])
            .order_by("-created_at")
            .first()
        )

        if otp is None or not otp.is_valid():
            raise serializers.ValidationError(
                {"code": "رمز التحقق غير صحيح أو انتهت صلاحيته."}
            )

        attrs["user"] = user
        attrs["otp"] = otp
        return attrs
    
class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(email__iexact=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "بيانات غير صحيحة"})

        otp = (
            OTP.objects.filter(
                user=user, code=attrs["code"], purpose=OTP.Purpose.EMAIL_VERIFICATION
            )
            .order_by("-created_at")
            .first()
        )

        if otp is None or not otp.is_valid():
            raise serializers.ValidationError({"code": "الكود غير صحيح أو منتهي الصلاحية"})

        attrs["user"] = user
        attrs["otp"] = otp
        return attrs