from django.urls import path
from .views import RegisterDeviceTokenView,NotificationListView

urlpatterns = [
    path("fcm-token/", RegisterDeviceTokenView.as_view(), name="register-device"),
    path("", NotificationListView.as_view(), name="notification-list"),
]