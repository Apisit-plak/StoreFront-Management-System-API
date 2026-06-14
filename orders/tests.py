from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserRole
from orders.models import Cart, Order, OrderItem
from products.models import Product
from tests.factories import create_product, create_user


class CartAndOrderAPITestCase(APITestCase):
    def setUp(self):
        self.seller = create_user("seller", role=UserRole.SELLER)
        self.buyer = create_user("buyer", role=UserRole.BUYER)
        self.product_a = create_product(self.seller, title="Product A", quantity=10, unit_price="20.00")
        self.product_b = create_product(self.seller, title="Product B", quantity=5, unit_price="30.00")
        self.client.force_authenticate(user=self.buyer)

    def test_buyer_gets_empty_cart_on_registration(self):
        cart = Cart.objects.get(user=self.buyer)
        response = self.client.get(reverse("cart-detail"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["cart"]["id"], cart.id)
        self.assertEqual(response.data["cart"]["item_count"], 0)

    def test_add_items_to_cart(self):
        response = self.client.post(
            reverse("cart-item-list-create"),
            {"product_id": self.product_a.id, "quantity": 2},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["item"]["quantity"], 2)

        response = self.client.post(
            reverse("cart-item-list-create"),
            {"product_id": self.product_b.id, "quantity": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        cart_response = self.client.get(reverse("cart-detail"))
        self.assertEqual(cart_response.data["cart"]["item_count"], 2)
        self.assertEqual(Decimal(cart_response.data["cart"]["total_amount"]), Decimal("70.00"))

    def test_adding_same_product_merges_quantities(self):
        self.client.post(
            reverse("cart-item-list-create"),
            {"product_id": self.product_a.id, "quantity": 2},
            format="json",
        )
        response = self.client.post(
            reverse("cart-item-list-create"),
            {"product_id": self.product_a.id, "quantity": 3},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["item"]["quantity"], 5)

    def test_checkout_creates_order_and_reduces_stock(self):
        self.client.post(
            reverse("cart-item-list-create"),
            {"product_id": self.product_a.id, "quantity": 2},
            format="json",
        )
        self.client.post(
            reverse("cart-item-list-create"),
            {"product_id": self.product_b.id, "quantity": 1},
            format="json",
        )

        response = self.client.post(reverse("cart-checkout"))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 2)

        order = Order.objects.first()
        self.assertEqual(order.total_amount, Decimal("70.00"))
        self.assertEqual(order.buyer, self.buyer)

        self.product_a.refresh_from_db()
        self.product_b.refresh_from_db()
        self.assertEqual(self.product_a.quantity, 8)
        self.assertEqual(self.product_b.quantity, 4)

        cart_response = self.client.get(reverse("cart-detail"))
        self.assertEqual(cart_response.data["cart"]["item_count"], 0)

    def test_checkout_fails_with_empty_cart(self):
        response = self.client.post(reverse("cart-checkout"))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_checkout_fails_when_stock_insufficient(self):
        self.client.post(
            reverse("cart-item-list-create"),
            {"product_id": self.product_b.id, "quantity": 4},
            format="json",
        )
        Product.objects.filter(pk=self.product_b.pk).update(quantity=2)

        response = self.client.post(reverse("cart-checkout"))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.product_b.refresh_from_db()
        self.assertEqual(self.product_b.quantity, 2)
        self.assertEqual(Order.objects.count(), 0)

    def test_seller_cannot_access_cart(self):
        self.client.force_authenticate(user=self.seller)
        response = self.client.get(reverse("cart-detail"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_buyer_can_list_order_history(self):
        self.client.post(
            reverse("cart-item-list-create"),
            {"product_id": self.product_a.id, "quantity": 1},
            format="json",
        )
        self.client.post(reverse("cart-checkout"))

        response = self.client.get(reverse("order-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
