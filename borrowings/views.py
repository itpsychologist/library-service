from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingReadSerializer


class BorrowingListView(generics.ListAPIView):
    """
    GET /api/borrowings/

    Повертає список запозичень. На цьому етапі (п.3) — без фільтрації
    за поточним користувачем і без query-параметрів `is_active` / `user_id`;
    розмежування видимості та фільтри додаються в п.5.
    """

    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingReadSerializer
    permission_classes = [IsAuthenticated]


class BorrowingDetailView(generics.RetrieveAPIView):
    """
    GET /api/borrowings/<id>/

    Повертає деталі одного запозичення разом із повною інформацією
    про книгу (nested BookSerializer).
    """

    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingReadSerializer
    permission_classes = [IsAuthenticated]
