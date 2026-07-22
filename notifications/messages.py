def new_order_nearby(shop_name):
    return {
        "title": "طلب توصيل جديد بالقرب منك",
        "body": f"طلب جديد من {shop_name} بانتظار من يقبله",
    }


def order_accepted(rep_name):
    return {
        "title": "تم قبول طلبك",
        "body": f"قام {rep_name} بقبول طلبك وهو في الطريق لاستلام الشحنة",
    }


def order_picked_up():
    return {
        "title": "تم استلام الشحنة",
        "body": "قام المندوب باستلام شحنتك وهي الآن في طريقها للعميل",
    }


def order_on_the_way():
    return {
        "title": "الشحنة في الطريق",
        "body": "شحنتك الآن في الطريق إلى العميل",
    }


def order_delivered(customer_name):
    return {
        "title": "تم تسليم الشحنة بنجاح",
        "body": f"تم تسليم طلب {customer_name} بنجاح",
    }


def order_cancelled_by_rep():
    return {
        "title": "اعتذار عن التوصيل",
        "body": "اعتذر المندوب عن استكمال طلبك، ويتم البحث عن مندوب آخر الآن",
    }


def order_cancelled_by_merchant():
    return {
        "title": "تم إلغاء الطلب",
        "body": "قام التاجر بإلغاء هذا الطلب",
    }