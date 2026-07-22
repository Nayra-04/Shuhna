from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Order, OrderStatusHistory
from .services import send_push_to_user
from . import messages


# apps/notifications/signals.py

@receiver(post_save, sender=OrderStatusHistory)
def handle_order_status_change(sender, instance, created, **kwargs):
    if not created:
        return

    order = instance.order
    status = instance.status
    changed_by = instance.changed_by

    if status == Order.Status.ACCEPTED:
        msg = messages.order_accepted(order.rep.full_name)
        send_push_to_user(order.merchant, **msg, notification_type="order_accepted", order_id=order.id)

    elif status == Order.Status.PICKED_UP:
        msg = messages.order_picked_up()
        send_push_to_user(order.merchant, **msg, notification_type="order_picked_up", order_id=order.id)

    elif status == Order.Status.ON_THE_WAY:
        msg = messages.order_on_the_way()
        send_push_to_user(order.merchant, **msg, notification_type="order_on_the_way", order_id=order.id)

    elif status == Order.Status.DELIVERED:
        msg = messages.order_delivered(order.customer_name)
        send_push_to_user(order.merchant, **msg, notification_type="order_delivered", order_id=order.id)

    elif status == Order.Status.CANCELLED:
        msg = messages.order_cancelled_by_merchant()
        if order.rep:
            send_push_to_user(order.rep, **msg, notification_type="order_cancelled", order_id=order.id)

    elif status == Order.Status.PENDING and changed_by and changed_by.role == "rep":
        msg = messages.order_cancelled_by_rep()
        send_push_to_user(order.merchant, **msg, notification_type="order_cancelled_by_rep", order_id=order.id)


@receiver(post_save, sender=Order)
def handle_new_order_created(sender, instance, created, **kwargs):
    if not created:
        return

    from django.contrib.gis.measure import D
    from users.models import User

    nearby_reps = User.objects.filter(
        role=User.Role.REP,
        rep_profile__current_location__distance_lte=(
            instance.merchant.merchant_profile.shop_location, D(km=5)
        ),
    )

    shop_name = instance.merchant.merchant_profile.shop_name
    msg = messages.new_order_nearby(shop_name)
    for rep in nearby_reps:
        send_push_to_user(rep, **msg, notification_type="new_order", order_id=instance.id)