from django.utils.translation import gettext_lazy as _
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Borrowing
from .serializers import (
    BorrowingReadSerializer,
    BorrowingCreateSerializer,
    BorrowingReturnSerializer,
)


def _parse_bool_param(value: str, param_name: str) -> bool:

    normalized = value.strip().lower()
    if normalized in ("true", "1"):
        return True
    if normalized in ("false", "0"):
        return False
    raise ValidationError(
        {param_name: _("Must be 'true' or 'false'.")}
    )


class BorrowingListView(generics.ListAPIView):

    serializer_class = BorrowingReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Borrowing.objects.select_related("book", "user")

        qs = qs if user.is_staff else qs.filter(user=user)

        is_active_param = self.request.query_params.get("is_active")
        if is_active_param is not None:
            is_active = _parse_bool_param(is_active_param, "is_active")
            qs = qs.filter(actual_return_date__isnull=is_active)

        user_id_param = self.request.query_params.get("user_id")
        if user_id_param is not None and user.is_staff:
            try:
                user_id = int(user_id_param)
            except (TypeError, ValueError):
                raise ValidationError(
                    {"user_id": _("Must be a valid integer.")}
                )
            qs = qs.filter(user_id=user_id)

        return qs


class BorrowingDetailView(generics.RetrieveAPIView):

    serializer_class = BorrowingReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Borrowing.objects.select_related("book", "user")


class BorrowingCreateView(generics.CreateAPIView):

    queryset = Borrowing.objects.all()
    serializer_class = BorrowingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class BorrowingListCreateDispatchView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return BorrowingListView.as_view()(request._request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return BorrowingCreateView.as_view()(request._request, *args, **kwargs)


class BorrowingReturnView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        borrowing = generics.get_object_or_404(
            Borrowing.objects.select_related("book", "user"), pk=pk
        )

        if not request.user.is_staff and borrowing.user_id != request.user.id:
            raise PermissionDenied(
                "You do not have permission to return this borrowing."
            )

        serializer = BorrowingReturnSerializer(instance=borrowing, data={})
        serializer.is_valid(raise_exception=True)
        updated_borrowing = serializer.save()

        response_serializer = BorrowingReadSerializer(updated_borrowing)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
