from rest_framework import serializers
from django.contrib.gis.geos import Point
from .models import Order,OrderStatusHistory
from .utils import calculate_delivery_fee


class OrderCreateSerializer(serializers.ModelSerializer):
    dropoff_lat = serializers.FloatField(write_only=True)
    dropoff_lng = serializers.FloatField(write_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "customer_name", "customer_phone", "delivery_address",
            "dropoff_lat", "dropoff_lng", "package_size", "notes",
            "delivery_fee", "distance_km", "status",
        ]
        read_only_fields = ["id", "delivery_fee", "distance_km", "status"]

    def validate(self, attrs):
        merchant = self.context["request"].user
        shop_location = getattr(merchant.merchant_profile, "shop_location", None)

        if shop_location is None:
            raise serializers.ValidationError(
                "يجب تحديد موقع المتجر الخاص بك من صفحة البروفايل قبل إنشاء طلب"
            )

        attrs["_pickup_location"] = shop_location
        return attrs

    def create(self, validated_data):
        dropoff_lat = validated_data.pop("dropoff_lat")
        dropoff_lng = validated_data.pop("dropoff_lng")
        pickup_location = validated_data.pop("_pickup_location")
        dropoff_location = Point(dropoff_lng, dropoff_lat, srid=4326)
        distance_km, delivery_fee = calculate_delivery_fee(pickup_location, dropoff_location)
        order = Order.objects.create(
            merchant=self.context["request"].user,
            dropoff_location=dropoff_location,
            distance_km=distance_km,
            delivery_fee=delivery_fee,
            **validated_data,
        )
        return order


class OrderListSerializer(serializers.ModelSerializer):
    dropoff_lat = serializers.SerializerMethodField()
    dropoff_lng = serializers.SerializerMethodField()
    merchant = serializers.CharField(source='merchant.full_name',read_only=True)
    rep = serializers.CharField(source='rep.full_name',read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = Order
        fields = [
            "id","order_number","merchant", "rep", "customer_name", "customer_phone",
            "delivery_address", "dropoff_lat", "dropoff_lng",
            "package_size", "delivery_fee", "distance_km",
            "status", "notes", "created_at", "updated_at",
        ]

    def get_dropoff_lat(self, obj):
        return obj.dropoff_location.y

    def get_dropoff_lng(self, obj):
        return obj.dropoff_location.x
    

class NearbyOrderSerializer(serializers.ModelSerializer):
    distance_to_merchant_km = serializers.SerializerMethodField()
    shop_location_lat = serializers.SerializerMethodField()
    shop_location_lng = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Order
        fields = [
            "id", "customer_name", "delivery_address",
            "package_size", "delivery_fee", "distance_km",
            "shop_location_lat", "shop_location_lng",
            "distance_to_merchant_km", "created_at",
        ]

    def get_distance_to_merchant_km(self, obj):
        return round(obj._distance.km, 5) if hasattr(obj, "_distance") else None

    def get_shop_location_lat(self, obj):
        return obj.merchant.merchant_profile.shop_location.y

    def get_shop_location_lng(self, obj):
        return obj.merchant.merchant_profile.shop_location.x
    

class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source="changed_by.full_name", read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = ["status", "changed_by_name", "created_at"]


class OrderDetailSerializer(OrderListSerializer):
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

    class Meta(OrderListSerializer.Meta):
        fields = OrderListSerializer.Meta.fields + ["status_history"]