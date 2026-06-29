from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book

User = get_user_model()


class BorrowingCreateNotificationTests(APITestCase):
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
        self.expected_return = (
            timezone.now().date() + timedelta(days=5)
        ).isoformat()

    @patch("borrowings.serializers.send_telegram_message")
    def test_creating_borrowing_sends_telegram_notification(self, mock_send):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            self.url,
            {"book": self.book.id, "expected_return_date": self.expected_return},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_send.assert_called_once()
        sent_text = mock_send.call_args[0][0]
        self.assertIn(self.user.email, sent_text)
        self.assertIn(self.book.title, sent_text)

    @patch("borrowings.serializers.send_telegram_message")
    def test_borrowing_creation_succeeds_regardless_of_notification(
        self, mock_send
    ):

        self.client.force_authenticate(self.user)
        response = self.client.post(
            self.url,
            {"book": self.book.id, "expected_return_date": self.expected_return},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 1)
