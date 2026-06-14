from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsBuyer
from products.filters import ProductFilter
from products.models import Product
from products.permissions import ProductPermission
from products.serializers import (
    ProductCreateUpdateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    PurchaseSerializer,
)
from products.services import purchase_product
from storefront.exceptions import InsufficientStockError


class ProductListCreateView(generics.ListCreateAPIView):
    permission_classes = (ProductPermission,)
    filterset_class = ProductFilter
    search_fields = ("title", "description")
    ordering_fields = ("unit_price", "created_at", "title", "quantity")
    ordering = ("-created_at",)

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related("seller")
        if self.request.user.role == "SELLER" and self.request.query_params.get("mine") == "true":
            return queryset.filter(seller=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductCreateUpdateSerializer
        return ProductListSerializer

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save(seller=request.user)
        return Response(
            {
                "success": True,
                "product": ProductDetailSerializer(product, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (ProductPermission,)
    queryset = Product.objects.select_related("seller")

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer


class ProductPurchaseView(APIView):
    permission_classes = (IsAuthenticated, IsBuyer)

    def post(self, request, pk):
        try:
            product = Product.objects.get(pk=pk, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {"success": False, "errors": {"detail": "Product not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data["quantity"]

        try:
            updated_product = purchase_product(product, quantity)
        except InsufficientStockError as exc:
            return Response(
                {
                    "success": False,
                    "errors": {
                        "quantity": str(exc),
                        "available": exc.available,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": f"Successfully purchased {quantity} unit(s) of '{product.title}'.",
                "product": ProductDetailSerializer(updated_product, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )
