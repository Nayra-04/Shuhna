from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.gis.geos import Point
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from users.permissions import IsRep
from orders.models import Order
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)
from .serializers import UpdateLocationRequestSerializer,UpdateLocationResponseSerializer, LastKnownLocationResponseSerializer

class UpdateLocationView(APIView):
    permission_classes = [IsAuthenticated, IsRep]
    @extend_schema(
        tags=["Tracking"],
        description="Update representative location using websocket",
        request=UpdateLocationRequestSerializer,
        responses=UpdateLocationResponseSerializer,
        
    )
    def post(self, request):
        lat = request.data.get("lat")
        lng = request.data.get("lng")

        if lat is None or lng is None:
            return Response(
                {"detail": "يجب إرسال lat و lng"}, status=status.HTTP_400_BAD_REQUEST
            )

        rep_profile = request.user.rep_profile
        rep_profile.current_location = Point(float(lng), float(lat), srid=4326)
        rep_profile.last_location_update = timezone.now()
        rep_profile.save(update_fields=["current_location", "last_location_update"])

        active_orders = Order.objects.filter(
            rep=request.user,
            status__in=[
                Order.Status.ACCEPTED,
                Order.Status.PICKED_UP,
                Order.Status.ON_THE_WAY,
            ],
        )

        channel_layer = get_channel_layer()
        for order in active_orders:
            async_to_sync(channel_layer.group_send)(
                f"order_tracking_{order.id}",
                {
                    "type": "location_update",
                    "lat": lat,
                    "lng": lng,
                    "updated_at": timezone.now().isoformat(),
                },
            )

        return Response({"detail": "تم تحديث الموقع"}, status=status.HTTP_200_OK)
    

class GetLastKnownLocationView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=["Tracking"],
        description="Get representative last location",
        request=UpdateLocationRequestSerializer,
        responses=LastKnownLocationResponseSerializer
    )
    def get(self, request, order_id):
        try:
            order = Order.objects.select_related("rep__rep_profile").get(pk=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "الطلب غير موجود"}, status=status.HTTP_404_NOT_FOUND)

        if order.merchant_id != request.user.id and order.rep_id != request.user.id:
            return Response(
                {"detail": "ليس لديك صلاحية على هذا الطلب"}, status=status.HTTP_403_FORBIDDEN
            )

        if order.rep is None or order.rep.rep_profile.current_location is None:
            return Response(
                {"detail": "لا يوجد موقع متاح حاليًا لهذا الطلب"},
                status=status.HTTP_404_NOT_FOUND,
            )

        rep_profile = order.rep.rep_profile
        return Response(
            {
                "lat": rep_profile.current_location.y,
                "lng": rep_profile.current_location.x,
                "last_updated": rep_profile.last_location_update,
            },
            status=status.HTTP_200_OK,
        )