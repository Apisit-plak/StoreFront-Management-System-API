from rest_framework import serializers

from accounts.models import UserRole
from products.models import Product


class ProductListSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.username", read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    stock_status = serializers.CharField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "title",
            "description",
            "unit_price",
            "quantity",
            "image",
            "seller",
            "seller_name",
            "in_stock",
            "stock_status",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("seller", "created_at", "updated_at")


class ProductDetailSerializer(ProductListSerializer):
    pass


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("title", "description", "unit_price", "quantity", "image", "is_active")

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value


class PurchaseSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, default=1)
