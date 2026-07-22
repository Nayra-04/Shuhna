from django.urls import path
from .views import UpdateLocationView,GetLastKnownLocationView

urlpatterns = [
    path("update-location/", UpdateLocationView.as_view(), name="update-location"),
    path("<uuid:order_id>/last-location/", GetLastKnownLocationView.as_view(), name="last-location"),
]