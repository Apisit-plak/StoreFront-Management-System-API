from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserRole


class AuthAPITestCase(APITestCase):
    def test_register_buyer_success(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "buyer1",
                "email": "buyer1@example.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "role": UserRole.BUYER,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["user"]["role"], UserRole.BUYER)

    def test_register_password_mismatch(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "buyer2",
                "email": "buyer2@example.com",
                "password": "SecurePass123!",
                "password_confirm": "DifferentPass123!",
                "role": UserRole.BUYER,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_login_returns_jwt_and_user(self):
        self.client.post(
            reverse("register"),
            {
                "username": "seller1",
                "email": "seller1@example.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "role": UserRole.SELLER,
            },
            format="json",
        )

        response = self.client.post(
            reverse("login"),
            {"username": "seller1", "password": "SecurePass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["role"], UserRole.SELLER)

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_returns_current_user(self):
        register_response = self.client.post(
            reverse("register"),
            {
                "username": "buyer3",
                "email": "buyer3@example.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "role": UserRole.BUYER,
            },
            format="json",
        )
        login_response = self.client.post(
            reverse("login"),
            {"username": "buyer3", "password": "SecurePass123!"},
            format="json",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], register_response.data["user"]["username"])
