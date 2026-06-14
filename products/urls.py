from django.urls import path

from products.views import ProductDetailView, ProductListCreateView, ProductPurchaseView

urlpatterns = [
    path("", ProductListCreateView.as_view(), name="product-list-create"),
    path("<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("<int:pk>/purchase/", ProductPurchaseView.as_view(), name="product-purchase"),
]
