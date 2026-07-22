import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class OrderTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]
        self.room_group_name = f"order_tracking_{self.order_id}"
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close(code=4001)
            return

        has_access = await self.user_has_access_to_order(user, self.order_id)
        if not has_access:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def location_update(self, event):
        await self.send(text_data=json.dumps({
            "lat": event["lat"],
            "lng": event["lng"],
            "updated_at": event["updated_at"],
        }))

    @database_sync_to_async
    def user_has_access_to_order(self, user, order_id):
        from orders.models import Order
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return False
        return order.merchant_id == user.id or order.rep_id == user.id