# users/tests/test_user_api.py
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

REGISTER_URL = reverse("users:register")
TOKEN_URL = reverse("users:token_obtain_pair")
ME_URL = reverse("users:manage_user")


class UserApiTests(APITestCase):
    def test_register_user_success(self):
        payload = {"email": "tests@example.com", "password": "testpass123"}
        res = self.client.post(REGISTER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_obtain_token_for_valid_credentials(self):
        get_user_model().objects.create_user(
            email="tests@example.com", password="testpass123"
        )
        res = self.client.post(
            TOKEN_URL,
            {"email": "tests@example.com", "password": "testpass123"},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_me_requires_authentication(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_own_profile(self):
        user = get_user_model().objects.create_user(
            email="tests@example.com", password="testpass123"
        )
        self.client.force_authenticate(user)
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], user.email)
