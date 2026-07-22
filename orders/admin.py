from django.contrib import admin
from django import forms
from .models import Order,OrderStatusHistory


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number","id", "customer_name", "status", "delivery_fee", "created_at"]
    list_filter = ["status", "package_size"]
    search_fields = ["customer_name", "customer_phone", "order_number"]

    formfield_overrides = {
        Order._meta.get_field("dropoff_location").__class__: {
            "widget": forms.Textarea(attrs={"rows": 2})
        },
    }

admin.site.register(OrderStatusHistory)