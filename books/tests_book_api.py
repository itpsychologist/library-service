from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book

BOOKS_URL = reverse("books:book-list")


def detail_url(book_id: int) -> str:
    return reverse("books:book-detail", args=[book_id])


def sample_book(**params) -> Book:
    defaults = {
        "title": "Sample Book",
        "author": "Sample Author",
        "cover": Book.Cover.SOFT,
        "inventory": 10,
        "daily_fee": Decimal("0.50"),
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


class AnonymousBookApiTests(APITestCase):
    """Анонімні користувачі: тільки читання."""

    def test_list_books_allowed(self):
        sample_book()
        res = self.client.get(BOOKS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_retrieve_book_allowed(self):
        book = sample_book()
        res = self.client.get(detail_url(book.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], book.title)

    def test_create_book_forbidden(self):
        payload = {
            "title": "New Book",
            "author": "New Author",
            "cover": Book.Cover.HARD,
            "inventory": 5,
            "daily_fee": "1.00",
        }
        res = self.client.post(BOOKS_URL, payload)
        self.assertIn(
            res.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_delete_book_forbidden(self):
        book = sample_book()
        res = self.client.delete(detail_url(book.id))
        self.assertIn(
            res.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )


class AuthenticatedNonStaffBookApiTests(APITestCase):
    """Звичайний автентифікований користувач: теж тільки читання."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(self.user)

    def test_create_book_forbidden(self):
        payload = {
            "title": "New Book",
            "author": "New Author",
            "cover": Book.Cover.HARD,
            "inventory": 5,
            "daily_fee": "1.00",
        }
        res = self.client.post(BOOKS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_book_forbidden(self):
        book = sample_book()
        res = self.client.patch(detail_url(book.id), {"inventory": 3})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookApiTests(APITestCase):
    """Staff-користувач: повний CRUD."""

    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            email="admin@example.com",
            password="adminpass123",
            is_staff=True,
        )
        self.client.force_authenticate(self.admin)

    def test_create_book(self):
        payload = {
            "title": "New Book",
            "author": "New Author",
            "cover": Book.Cover.HARD,
            "inventory": 5,
            "daily_fee": "1.00",
        }
        res = self.client.post(BOOKS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Book.objects.filter(title="New Book").exists())

    def test_update_book_inventory(self):
        book = sample_book(inventory=10)
        res = self.client.patch(detail_url(book.id), {"inventory": 7})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        book.refresh_from_db()
        self.assertEqual(book.inventory, 7)

    def test_delete_book(self):
        book = sample_book()
        res = self.client.delete(detail_url(book.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=book.id).exists())
