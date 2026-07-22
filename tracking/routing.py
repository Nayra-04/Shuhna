from django.urls import re_path
from .consumers import OrderTrackingConsumer

websocket_urlpatterns = [
    re_path(r"ws/tracking/(?P<order_id>[0-9a-f-]+)/$", OrderTrackingConsumer.as_asgi()),
]