from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User
from users.permissions import IsMerchant, IsRep
from .models import Order, OrderStatusHistory
from .serializers import OrderCreateSerializer, OrderListSerializer, NearbyOrderSerializer, OrderStatusUpdateSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiTypes
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.db import transaction
from .services import transition_order_status,accept_order



@extend_schema(tags=["Orders"])
class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated, IsMerchant]

    @extend_schema(
        description="Create a new delivery order.",
        request=OrderCreateSerializer,
    )
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderListSerializer(order).data, status=status.HTTP_201_CREATED)

@extend_schema(tags=["Orders"])
class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Returns orders for the authenticated user. Merchants see their created orders, reps see assigned orders.",
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter orders by status",
                enum=[choice[0] for choice in Order.Status.choices],
            ),
        ],
        responses={200: OrderListSerializer(many=True)},
    )
    def get(self, request):
        user = request.user

        if user.role == "merchant":
            orders = Order.objects.filter(merchant=user)
        else:
            orders = Order.objects.filter(rep=user)

        orders = orders.select_related("merchant", "rep")

        status_param = request.query_params.get("status")
        if status_param:
            valid_statuses = [choice[0] for choice in Order.Status.choices]
            if status_param not in valid_statuses:
                return Response(
                    {"detail": f"قيمة status غير صحيحة. القيم المسموحة: {valid_statuses}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            orders = orders.filter(status=status_param)

        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(tags=["Orders"])
class OrderRetrieveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Retrieve a single order by UUID.",
        responses={
            200: OrderListSerializer,
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Order not found"),
        },
    )
    def get(self, request, pk):
        try:
            order = Order.objects.select_related("merchant", "rep").get(pk=pk)
        except Order.DoesNotExist:
            return Response({"detail": "الطلب غير موجود"}, status=status.HTTP_404_NOT_FOUND)

        if order.merchant_id != request.user.id and order.rep_id != request.user.id:
            return Response({"detail": "غير مصرح لك برؤية هذا الطلب"}, status=status.HTTP_403_FORBIDDEN)

        return Response(OrderListSerializer(order).data, status=status.HTTP_200_OK)
    
@extend_schema(tags=["Orders"])
class NearbyOrdersView(APIView):
    permission_classes = [IsAuthenticated, IsRep]

    def get(self, request):
        rep_profile = getattr(request.user, "rep_profile", None)
        if rep_profile is None or rep_profile.current_location is None:
            return Response(
                {"detail": "يجب تحديد موقعك الحالي أولاً من صفحة البروفايل"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        radius_km = float(request.query_params.get("radius", 10))
        rep_location = rep_profile.current_location

        orders = (
            Order.objects.filter(
                status=Order.Status.PENDING,
                merchant__merchant_profile__shop_location__distance_lte=(
                    rep_location, D(km=radius_km)
                ),
            )
            .annotate(_distance=Distance("merchant__merchant_profile__shop_location", rep_location))
            .select_related("merchant", "merchant__merchant_profile")
            .order_by("_distance")
        )

        serializer = NearbyOrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

@extend_schema(tags=["Orders"])
class OrderStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        description="Update Orders Status",
        request=OrderStatusUpdateSerializer
    )
    def patch(self, request, pk):
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]

        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().get(pk=pk)
            except Order.DoesNotExist:
                return Response({"detail": "الطلب غير موجود"}, status=status.HTTP_404_NOT_FOUND)

            updated_order = transition_order_status(order, new_status, request.user)

        return Response(OrderListSerializer(updated_order).data, status=status.HTTP_200_OK)

@extend_schema(tags=["Orders"])
class AcceptOrderView(APIView):
    permission_classes = [IsAuthenticated, IsRep]
    def post(self, request, pk):
        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().get(pk=pk)
            except Order.DoesNotExist:
                return Response({"detail": "الطلب غير موجود"}, status=status.HTTP_404_NOT_FOUND)

            updated_order = accept_order(order, request.user)

        return Response(OrderListSerializer(updated_order).data, status=status.HTTP_200_OK)
    

class RecentOrdersView(APIView):
    permission_classes = [IsAuthenticated, IsMerchant]

    @extend_schema(
        description="Returns the most recent orders for the authenticated merchant.",
        parameters=[
            OpenApiParameter(
                name="limit",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Number of recent orders to return.",
                default=3,
            ),
        ],
        responses={
            200: OrderListSerializer(many=True),
        },
        tags=["Orders"],
    )
    def get(self, request):
        limit = int(request.query_params.get("limit", 3))

        orders = (
            Order.objects.filter(merchant=request.user)
            .select_related("rep")
            .order_by("-created_at")[:limit]
        )

        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class RepOrderStatsView(APIView):
    permission_classes = [IsAuthenticated, IsRep]

    @extend_schema(
        description="Returns completed, active, and cancelled order counts for the authenticated representative.",
        tags=["Orders"],
    )
    def get(self, request):
        completed_count = Order.objects.filter(
            rep=request.user, status=Order.Status.DELIVERED
        ).count()

        active_count = Order.objects.filter(
            rep=request.user,
            status__in=[
                Order.Status.ACCEPTED,
                Order.Status.PICKED_UP,
                Order.Status.ON_THE_WAY,
            ],
        ).count()

        abandoned_count = OrderStatusHistory.objects.filter(
            changed_by=request.user, status=Order.Status.PENDING
        ).count()

        return Response(
            {
                "completed_orders": completed_count,
                "active_orders": active_count,
                "abandoned_orders": abandoned_count,
            },
            status=status.HTTP_200_OK,
        )