from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from .managers import UserManager
from django.contrib.gis.db import models
import random
from datetime import timedelta
from django.conf import settings
from django.utils import timezone


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        MERCHANT = "merchant", "Merchant"
        REP = "rep", "Rep"

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150)
    image = models.ImageField(upload_to="profile_images/", null=True, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "phone"]

    def __str__(self):
        return f"{self.full_name} ({self.email})"
    


class MerchantProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="merchant_profile"
    )
    shop_name = models.CharField(max_length=150)
    shop_address = models.CharField(max_length=255, blank=True)
    shop_location = models.PointField(
        geography=True,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.shop_name


class RepProfile(models.Model):
    class VehicleType(models.TextChoices):
        MOTORCYCLE = "motorcycle", "Motorcycle"
        CAR = "car", "Car"
        BICYCLE = "bicycle", "Bicycle"
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="rep_profile"
    )
    vehicle_type = models.CharField(
        max_length=20, choices=VehicleType.choices, blank=True
    )
    # is_available = models.BooleanField(default=True)
    current_location = models.PointField(
        geography=True,
        null=True,
        blank=True,
    )
    last_location_update = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.full_name}"
    


class OTP(models.Model):
    class Purpose(models.TextChoices):
        EMAIL_VERIFICATION = "email_verification", "Email Verification"
        PASSWORD_RESET = "password_reset", "Password Reset"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="otps"
    )
    purpose = models.CharField(max_length=30, choices=Purpose.choices)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    @classmethod
    def generate_for_user(cls, user, purpose):
        code = f"{random.randint(0, 999999):06d}"
        return cls.objects.create(
            user=user,
            purpose=purpose,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

    def __str__(self):
        return f"{self.user.email} - {self.purpose} - {self.code}"