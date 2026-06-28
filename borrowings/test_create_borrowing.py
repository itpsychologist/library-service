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


class BorrowingCreateTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="reader@example.com", password="testpass123"
        )
        self.book = Book.objects.create(
            title="Clean Code",
            author="Robert Martin",
            cover=Book.Cover.HARD,
            inventory=2,
            daily_fee=Decimal("1.50"),
        )
        self.url = reverse("borrowings:borrowing-list-create")

    def test_unauthenticated_cannot_create(self):
        response = self.client.post(
            self.url,
            {"book": self.book.id, "expected_return_date": "2026-07-10"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_can_create_and_inventory_decreases(self):
        self.client.force_authenticate(self.user)
        expected_return = (timezone.now().date() + timedelta(days=5)).isoformat()

        response = self.client.post(
            self.url,
            {"book": self.book.id, "expected_return_date": expected_return},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 1)

        borrowing = Borrowing.objects.get(pk=response.data["id"])
        self.assertEqual(borrowing.user, self.user)
        self.assertEqual(borrowing.book, self.book)

    def test_cannot_create_when_inventory_zero(self):
        self.book.inventory = 0
        self.book.save()
        self.client.force_authenticate(self.user)
        expected_return = (timezone.now().date() + timedelta(days=5)).isoformat()

        response = self.client.post(
            self.url,
            {"book": self.book.id, "expected_return_date": expected_return},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 0)

    def test_cannot_set_user_field_manually(self):
        other_user = User.objects.create_user(
            email="other@example.com", password="testpass123"
        )
        self.client.force_authenticate(self.user)
        expected_return = (timezone.now().date() + timedelta(days=5)).isoformat()

        response = self.client.post(
            self.url,
            {
                "book": self.book.id,
                "expected_return_date": expected_return,
                "user": other_user.id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        borrowing = Borrowing.objects.get(pk=response.data["id"])
        self.assertEqual(borrowing.user, self.user)  # не other_user

    def test_list_returns_only_own_borrowings_for_non_staff(self):
        Borrowing.objects.create(
            book=self.book,
            user=self.user,
            expected_return_date=timezone.now().date() + timedelta(days=3),
        )
        other_user = User.objects.create_user(
            email="other2@example.com", password="testpass123"
        )
        Borrowing.objects.create(
            book=self.book,
            user=other_user,
            expected_return_date=timezone.now().date() + timedelta(days=3),
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_user_ids = {
            item["user"] for item in response.data["results"]
        }
        self.assertEqual(returned_user_ids, {self.user.id})