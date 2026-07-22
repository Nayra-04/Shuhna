from decimal import Decimal

from django.conf import settings
from django.contrib.gis.geos import Point
from geopy.distance import geodesic


def calculate_delivery_fee(pickup_location: Point, dropoff_location: Point):

    pickup_coords = (pickup_location.y, pickup_location.x)  
    dropoff_coords = (dropoff_location.y, dropoff_location.x)

    distance_km = Decimal(str(geodesic(pickup_coords, dropoff_coords).km))
    distance_km = round(distance_km, 2)

    fee = Decimal(settings.DELIVERY_BASE_FEE) + (
        distance_km * Decimal(settings.DELIVERY_PRICE_PER_KM)
    )
    fee = round(fee, 2)

    return distance_km, fee