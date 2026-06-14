from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsBuyer
from orders.models import Cart, CartItem, Order
from orders.serializers import CartItemSerializer, CartSerializer, OrderSerializer
from orders.services import checkout_cart
from storefront.exceptions import InsufficientStockError


class CartDetailView(APIView):
    permission_classes = (IsAuthenticated, IsBuyer)

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart, context={"request": request})
        return Response({"success": True, "cart": serializer.data})


class CartItemListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsBuyer)
    serializer_class = CartItemSerializer

    def get_cart(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def get_queryset(self):
        return CartItem.objects.filter(cart=self.get_cart()).select_related("product", "product__seller")

    def perform_create(self, serializer):
        cart = self.get_cart()
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data.get("quantity", 1)

        existing_item = CartItem.objects.filter(cart=cart, product=product).first()
        if existing_item:
            new_quantity = existing_item.quantity + quantity
            if product.quantity < new_quantity:
                from rest_framework.exceptions import ValidationError

                raise ValidationError(
                    {
                        "quantity": (
                            f"Insufficient stock for '{product.title}'. "
                            f"Available: {product.quantity}, "
                            f"already in cart: {existing_item.quantity}."
                        )
                    }
                )
            existing_item.quantity = new_quantity
            existing_item.save(update_fields=["quantity", "updated_at"])
            serializer.instance = existing_item
        else:
            serializer.save(cart=cart)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {
                "success": True,
                "item": CartItemSerializer(serializer.instance, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, IsBuyer)
    serializer_class = CartItemSerializer

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user).select_related(
            "product", "product__seller"
        )


class CheckoutView(APIView):
    permission_classes = (IsAuthenticated, IsBuyer)

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)

        try:
            order = checkout_cart(cart)
        except ValueError as exc:
            return Response(
                {"success": False, "errors": {"detail": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except InsufficientStockError as exc:
            return Response(
                {
                    "success": False,
                    "errors": {
                        "detail": str(exc),
                        "available": exc.available,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Order placed successfully.",
                "order": OrderSerializer(order, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class OrderListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsBuyer)
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).prefetch_related(
            "items", "items__product"
        )


class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsBuyer)
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).prefetch_related(
            "items", "items__product"
        )
