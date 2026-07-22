from django.urls import path
from .views import (
    OrderCreateView, 
    OrderListView, 
    OrderRetrieveView, 
    NearbyOrdersView, 
    OrderStatusUpdateView,
    AcceptOrderView,
    RecentOrdersView,
    RepOrderStatsView,
    )

urlpatterns = [
    path("create/", OrderCreateView.as_view(), name="order-create"),
    path("", OrderListView.as_view(), name="order-list"),
    path("<uuid:pk>/", OrderRetrieveView.as_view(), name="order-detail"),
    path("nearby/", NearbyOrdersView.as_view(), name="order-nearby"),
    path("<uuid:pk>/status/", OrderStatusUpdateView.as_view(), name="order-status-update"),
    path("<uuid:pk>/accept/", AcceptOrderView.as_view(), name="order-accept"),
    path("recent/", RecentOrdersView.as_view(), name="order-recent"),
    path("stats/", RepOrderStatsView.as_view(), name="order-stats"),
]