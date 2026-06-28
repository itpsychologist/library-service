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


def return_url(borrowing_id: int) -> str:
    return reverse("borrowings:borrowing-return", args=[borrowing_id])


class BorrowingReturnTests(APITestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title="Clean Code",
            author="Robert Martin",
            cover=Book.Cover.HARD,
            inventory=1,
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
        self.borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=timezone.now().date() + timedelta(days=5),
        )

    def test_anonymous_cannot_return(self):
        response = self.client.post(return_url(self.borrowing.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_can_return_and_inventory_increases(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(return_url(self.borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["actual_return_date"])

        self.borrowing.refresh_from_db()
        self.book.refresh_from_db()
        self.assertEqual(
            self.borrowing.actual_return_date, timezone.now().date()
        )
        self.assertEqual(self.book.inventory, 2)  # було 1, +1 при поверненні

    def test_cannot_return_twice(self):
        self.client.force_authenticate(self.user)
        self.client.post(return_url(self.borrowing.id))  # перше повернення

        response = self.client.post(return_url(self.borrowing.id))  # друге

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 2)  # не зросло вдруге

    def test_other_user_cannot_return_foreign_borrowing(self):
        self.client.force_authenticate(self.other_user)

        response = self.client.post(return_url(self.borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.borrowing.refresh_from_db()
        self.assertIsNone(self.borrowing.actual_return_date)

    def test_staff_can_return_foreign_borrowing(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(return_url(self.borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.borrowing.refresh_from_db()
        self.assertIsNotNone(self.borrowing.actual_return_date)

    def test_return_nonexistent_borrowing_returns_404(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(return_url(999999))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
