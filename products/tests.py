from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserRole
from products.models import Product
from tests.factories import create_product, create_test_image, create_user


class ProductAPITestCase(APITestCase):
    def setUp(self):
        self.seller = create_user("seller", role=UserRole.SELLER)
        self.buyer = create_user("buyer", role=UserRole.BUYER)
        self.other_seller = create_user("seller2", role=UserRole.SELLER)

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_seller_can_create_product(self):
        self.authenticate(self.seller)
        response = self.client.post(
            reverse("product-list-create"),
            {
                "title": "Wireless Mouse",
                "description": "Ergonomic wireless mouse",
                "unit_price": "29.99",
                "quantity": 50,
                "image": create_test_image(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Product.objects.first().seller, self.seller)

    def test_buyer_cannot_create_product(self):
        self.authenticate(self.buyer)
        response = self.client.post(
            reverse("product-list-create"),
            {
                "title": "Blocked Product",
                "description": "Should not be created",
                "unit_price": "10.00",
                "quantity": 5,
                "image": create_test_image(),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Product.objects.count(), 0)

    def test_buyer_can_list_and_filter_products(self):
        create_product(self.seller, title="Cheap Item", unit_price="5.00", quantity=10)
        create_product(self.seller, title="Premium Item", unit_price="100.00", quantity=0)

        self.authenticate(self.buyer)
        response = self.client.get(reverse("product-list-create"), {"min_price": "50", "in_stock": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

        response = self.client.get(reverse("product-list-create"), {"max_price": "10"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Cheap Item")

    def test_seller_can_only_update_own_product(self):
        product = create_product(self.seller, title="Owned Product")
        self.authenticate(self.other_seller)

        response = self.client.patch(
            reverse("product-detail", kwargs={"pk": product.pk}),
            {"title": "Hijacked"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        product.refresh_from_db()
        self.assertEqual(product.title, "Owned Product")

    def test_buyer_purchase_decreases_inventory(self):
        product = create_product(self.seller, quantity=10, unit_price="15.00")
        self.authenticate(self.buyer)

        response = self.client.post(
            reverse("product-purchase", kwargs={"pk": product.pk}),
            {"quantity": 3},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.quantity, 7)

    def test_purchase_fails_when_insufficient_stock(self):
        product = create_product(self.seller, quantity=2)
        self.authenticate(self.buyer)

        response = self.client.post(
            reverse("product-purchase", kwargs={"pk": product.pk}),
            {"quantity": 5},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        product.refresh_from_db()
        self.assertEqual(product.quantity, 2)

    def test_product_detail_shows_stock_status(self):
        product = create_product(self.seller, quantity=3)
        self.authenticate(self.buyer)

        response = self.client.get(reverse("product-detail", kwargs={"pk": product.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stock_status"], "low_stock")
        self.assertEqual(response.data["unit_price"], Decimal("19.99"))
