from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models
import uuid
from django.utils import timezone


class Order(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        PICKED_UP = "picked_up", "Picked Up"
        ON_THE_WAY = "on_the_way", "On The Way"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class PackageSize(models.TextChoices):
        SMALL = "small", "Small"
        MEDIUM = "medium", "Medium"
        LARGE = "large", "Large"

    merchant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders_created",
    )
    rep = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_assigned",
    )

    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    delivery_address = models.CharField(max_length=255)
    dropoff_location = gis_models.PointField(geography=True)

    package_size = models.CharField(max_length=10, choices=PackageSize.choices)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, editable=False)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, editable=False)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    order_number = models.CharField(max_length=20, editable=False, blank=True, null=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    def _generate_order_number(self):
        today_str = timezone.now().strftime("%Y%m%d")
        today_count = Order.objects.filter(
            created_at__date=timezone.now().date()
        ).count() + 1
        return f"ORD-{today_str}-{today_count:04d}"

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name} ({self.status})"
    

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="status_history"
    )
    status = models.CharField(max_length=20, choices=Order.Status.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.order.order_number} → {self.status}"