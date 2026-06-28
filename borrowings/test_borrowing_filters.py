from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from borrowings.models import Borrowing

User = get_user_model()


class BorrowingFilterTests(APITestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title="Clean Code",
            author="Robert Martin",
            cover=Book.Cover.HARD,
            inventory=10,
            daily_fee=Decimal("1.50"),
        )
        self.user = User.objects.create_user(
            email="reader@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com", password="testpass123"
        )
        self.admin = User.objects.create_user(
            email="admin@example.com", password="adminpass123", is_staff=True
        )

        today = timezone.now().date()

        # Активне запозичення поточного user
        self.active_own = Borrowing.objects.create(
            book=self.book, user=self.user,
            expected_return_date=today + timedelta(days=5),
        )
        # Повернене запозичення поточного user
        self.returned_own = Borrowing.objects.create(
            book=self.book, user=self.user,
            expected_return_date=today + timedelta(days=5),
            actual_return_date=today,
        )
        # Активне запозичення іншого user
        self.active_other = Borrowing.objects.create(
            book=self.book, user=self.other_user,
            expected_return_date=today + timedelta(days=3),
        )

        self.url = reverse("borrowings:borrowing-list-create")

    def _ids(self, response_data):
        results = response_data.get("results", response_data)
        return {item["id"] for item in results}

    # --- базова видимість (успадкована з п.4, перевіряємо що не зламали) ---

    def test_non_staff_sees_only_own_borrowings(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self._ids(response.data),
            {self.active_own.id, self.returned_own.id},
        )

    def test_staff_sees_all_borrowings_by_default(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self._ids(response.data),
            {self.active_own.id, self.returned_own.id, self.active_other.id},
        )

    # --- is_active ---

    def test_is_active_true_returns_only_not_returned(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url, {"is_active": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self._ids(response.data),
            {self.active_own.id, self.active_other.id},
        )

    def test_is_active_false_returns_only_returned(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url, {"is_active": "false"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._ids(response.data), {self.returned_own.id})

    def test_invalid_is_active_returns_400(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, {"is_active": "maybe"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- user_id (тільки для staff) ---

    def test_staff_can_filter_by_user_id(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url, {"user_id": self.other_user.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._ids(response.data), {self.active_other.id})

    def test_non_staff_user_id_param_is_ignored(self):
        self.client.force_authenticate(self.user)
        # Навіть якщо non-staff підставить чужий user_id — бачить лише своє.
        response = self.client.get(self.url, {"user_id": self.other_user.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self._ids(response.data),
            {self.active_own.id, self.returned_own.id},
        )

    def test_staff_invalid_user_id_returns_400(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url, {"user_id": "not-an-int"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- комбінація обох параметрів ---

    def test_staff_can_combine_user_id_and_is_active(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(
            self.url, {"user_id": self.user.id, "is_active": "false"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._ids(response.data), {self.returned_own.id})

    # --- доступ ---

    def test_anonymous_cannot_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
