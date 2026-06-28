from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from borrowings.models import Borrowing

User = get_user_model()


class BorrowingListDetailTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="reader@example.com", password="pass12345"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com", password="pass12345"
        )
        self.book = Book.objects.create(
            title="Clean Code",
            author="Robert Martin",
            cover=Book.Cover.SOFT,
            inventory=3,
            daily_fee="0.50",
        )
        self.borrowing = Borrowing.objects.create(
            expected_return_date=date.today() + timedelta(days=7),
            book=self.book,
            user=self.user,
        )

    def test_list_requires_authentication(self):
        url = reverse("borrowings:borrowing-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_nested_book_info(self):
        self.client.force_authenticate(self.user)
        url = reverse("borrowings:borrowing-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["book"]["title"], "Clean Code")
        self.assertEqual(results[0]["book"]["author"], "Robert Martin")

    def test_detail_returns_nested_book_info(self):
        self.client.force_authenticate(self.user)
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["book"]["title"], "Clean Code")
        self.assertIn("daily_fee", response.data["book"])

    def test_detail_requires_authentication(self):
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
