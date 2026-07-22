import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings

from .models import DeviceToken, Notification

if not firebase_admin._apps:
    cred = credentials.Certificate(str(settings.FIREBASE_CREDENTIALS_PATH))
    firebase_admin.initialize_app(cred)


def send_push_to_user(user, title, body, notification_type="", order_id=None):
    # 1. نخزن السجل في الداتابيز أولًا (عشان يظهر في الـ endpoint حتى لو الـ push فشل)
    Notification.objects.create(
        user=user,
        title=title,
        body=body,
        notification_type=notification_type,
        order_id=order_id,
    )

    # 2. نبعت الـ push الفعلي
    tokens = list(DeviceToken.objects.filter(user=user).values_list("token", flat=True))
    if not tokens:
        return

    for token in tokens:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={"type": notification_type, "order_id": str(order_id or "")},
            token=token,
        )
        try:
            messaging.send(message)
        except Exception as e:
            print(f"Failed to send notification to token {token[:20]}...: {e}")