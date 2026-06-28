from rest_framework import generics, permissions
from rest_framework.views import APIView

from .models import Borrowing
from .serializers import BorrowingReadSerializer, BorrowingCreateSerializer


class BorrowingListView(generics.ListAPIView):
    """GET /api/borrowings/ — реалізовано в п.3."""

    serializer_class = BorrowingReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Повна логіка фільтрації (is_active, user_id для staff) — у п.5.
        # Тут лишається базове розмежування "свої / усі", щоб п.4 не
        # розкривав чужі запозичення вже на цьому етапі.
        user = self.request.user
        qs = Borrowing.objects.select_related("book", "user")
        return qs if user.is_staff else qs.filter(user=user)


class BorrowingDetailView(generics.RetrieveAPIView):
    """GET /api/borrowings/<id>/ — реалізовано в п.3."""

    serializer_class = BorrowingReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Borrowing.objects.select_related("book", "user")


class BorrowingCreateView(generics.CreateAPIView):
    """
    POST /api/borrowings/ — новий, п.4.

    Створює нове запозичення для поточного автентифікованого користувача.
    Книга береться з тіла запиту (`book` — id), `user` підставляється
    автоматично з request.user — клієнт не може його передати.
    """

    queryset = Borrowing.objects.all()
    serializer_class = BorrowingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class BorrowingListCreateDispatchView(APIView):
    """
    Тонка диспетчерська обгортка над двома окремими views.

    Існує лише тому, що Django вимагає рівно один view-клас на path().
    Бізнес-логіка повністю лежить у BorrowingListView/BorrowingCreateView —
    цей клас нічого не вирішує сам, лише делегує виклик за HTTP-методом.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return BorrowingListView.as_view()(request._request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return BorrowingCreateView.as_view()(request._request, *args, **kwargs)
