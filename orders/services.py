from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import Order, OrderStatusHistory


ALLOWED_TRANSITIONS = {
    Order.Status.PENDING: [Order.Status.ACCEPTED, Order.Status.CANCELLED],
    Order.Status.ACCEPTED: [Order.Status.PICKED_UP, Order.Status.CANCELLED, Order.Status.PENDING],
    Order.Status.PICKED_UP: [Order.Status.ON_THE_WAY],
    Order.Status.ON_THE_WAY: [Order.Status.DELIVERED],
    Order.Status.DELIVERED: [],
    Order.Status.CANCELLED: [],
}


def _log_status_change(order, user):
    OrderStatusHistory.objects.create(
        order=order, status=order.status, changed_by=user
    )

def transition_order_status(order: Order, new_status: str, user):
    current_status = order.status

    allowed_next_statuses = ALLOWED_TRANSITIONS.get(current_status, [])
    if new_status not in allowed_next_statuses:
        raise ValidationError(
            f"لا يمكن تغيير حالة الطلب من '{current_status}' إلى '{new_status}'"
        )

    is_merchant_owner = order.merchant_id == user.id
    is_assigned_rep = order.rep_id == user.id

    if not is_merchant_owner and not is_assigned_rep:
        raise PermissionDenied("ليس لديك صلاحية على هذا الطلب")

    if new_status == Order.Status.CANCELLED:
        if current_status == Order.Status.PENDING and not is_merchant_owner:
            raise PermissionDenied("التاجر فقط يمكنه إلغاء الطلب في هذه المرحلة")

    elif new_status == Order.Status.PENDING:
        if not is_assigned_rep:
            raise PermissionDenied("فقط المندوب المسؤول يمكنه التراجع عن هذا الطلب")
        order.rep = None

    elif new_status in [Order.Status.PICKED_UP, Order.Status.ON_THE_WAY, Order.Status.DELIVERED]:
        if not is_assigned_rep:
            raise PermissionDenied("المندوب المسؤول عن الطلب فقط يمكنه تحديث هذه الحالة")

    order.status = new_status
    order.save(update_fields=["status", "rep", "updated_at"])
    _log_status_change(order, user)
    return order


def accept_order(order: Order, rep_user):
    if order.status != Order.Status.PENDING:
        raise ValidationError("هذا الطلب لم يعد متاحًا للقبول")

    if rep_user.role != "rep":
        raise PermissionDenied("هذا الإجراء متاح للمندوبين فقط")

    order.rep = rep_user
    order.status = Order.Status.ACCEPTED
    order.save(update_fields=["rep", "status", "updated_at"])
    _log_status_change(order, rep_user)
    return order