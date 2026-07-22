from rest_framework import serializers
from .models import DeviceToken,Notification


class RegisterDeviceTokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)

    def create(self, validated_data):
        user = self.context["request"].user
        device_token, _ = DeviceToken.objects.update_or_create(
            token=validated_data["token"],
            defaults={"user": user},
        )
        return device_token
    

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "body", "notification_type", "order_id", "is_read", "created_at"]