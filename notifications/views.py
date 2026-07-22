from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .serializers import RegisterDeviceTokenSerializer, NotificationSerializer
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)
from .models import Notification

class RegisterDeviceTokenView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=["Notifications"],
        description="Create FCM-Token for users",
        request=RegisterDeviceTokenSerializer
    )
    def post(self, request):
        serializer = RegisterDeviceTokenSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "تم تسجيل رمز الإشعارات"}, status=status.HTTP_200_OK)
    



class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=["Notifications"],
        description="Get all notifications for authenticated user.",
        responses={200: NotificationSerializer(many=True)},
    )
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
