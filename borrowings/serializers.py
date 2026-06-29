from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from books.serializers import BookSerializer
from notifications.telegram import send_telegram_message
from .models import Borrowing


class BorrowingReadSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )
        read_only_fields = fields


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "expected_return_date", "book")
        read_only_fields = ("id",)

    def validate_expected_return_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError(
                "Expected return date cannot be in the past."
            )
        return value

    def validate(self, attrs):
        book = attrs["book"]
        if book.inventory <= 0:
            raise serializers.ValidationError(
                {"book": f"Book '{book.title}' is out of stock right now."}
            )
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            book = validated_data["book"]

            book = type(book).objects.select_for_update().get(pk=book.pk)
            if book.inventory <= 0:
                raise serializers.ValidationError(
                    {"book": f"Book '{book.title}' is out of stock right now."}
                )

            book.inventory -= 1
            book.save(update_fields=["inventory"])

            borrowing = Borrowing.objects.create(
                book=book,
                expected_return_date=validated_data["expected_return_date"],
                user=self.context["request"].user,
            )

        self._notify_new_borrowing(borrowing)

        return borrowing

    @staticmethod
    def _notify_new_borrowing(borrowing: Borrowing) -> None:
        text = (
            "📚 Нове запозичення\n"
            f"Користувач: {borrowing.user.email}\n"
            f"Книга: {borrowing.book.title} ({borrowing.book.author})\n"
            f"Дата видачі: {borrowing.borrow_date}\n"
            f"Очікувана дата повернення: {borrowing.expected_return_date}"
        )
        send_telegram_message(text)

class BorrowingReturnSerializer(serializers.Serializer):

    def validate(self, attrs):
        borrowing: Borrowing = self.instance

        if borrowing.actual_return_date is not None:
            raise serializers.ValidationError(
                "This borrowing is already returned."
            )
        return attrs

    def save(self, **kwargs):
        borrowing: Borrowing = self.instance

        with transaction.atomic():

            borrowing = (
                Borrowing.objects.select_for_update().get(pk=borrowing.pk)
            )
            if borrowing.actual_return_date is not None:
                raise serializers.ValidationError(
                    "This borrowing is already returned."
                )

            borrowing.actual_return_date = timezone.now().date()
            borrowing.save(update_fields=["actual_return_date"])

            book = type(borrowing.book).objects.select_for_update().get(
                pk=borrowing.book_id
            )
            book.inventory += 1
            book.save(update_fields=["inventory"])

        return borrowing
