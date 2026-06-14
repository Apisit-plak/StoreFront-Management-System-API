from django.urls import path

from orders.views import (
    CartDetailView,
    CartItemDetailView,
    CartItemListCreateView,
    CheckoutView,
    OrderDetailView,
    OrderListView,
)

urlpatterns = [
    path("cart/", CartDetailView.as_view(), name="cart-detail"),
    path("cart/items/", CartItemListCreateView.as_view(), name="cart-item-list-create"),
    path("cart/items/<int:pk>/", CartItemDetailView.as_view(), name="cart-item-detail"),
    path("cart/checkout/", CheckoutView.as_view(), name="cart-checkout"),
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
]
