from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from books.serializers import BookSerializer
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
    """
    Серіалізатор для створення запозичення.

    Поле `user` НЕ приймається з запиту — воно береться з request.user
    у create(), щоб виключити можливість "позичити книгу за когось іншого".
    """

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
        # Транзакція гарантує атомарність: або і inventory зменшується,
        # і Borrowing створюється — або нічого з цього не відбувається.
        with transaction.atomic():
            book = validated_data["book"]

            # select_for_update — захист від race condition при паралельних
            # запитах на останній екземпляр книги (важливо навіть для
            # навчального проєкту, бо "5 concurrent users" з NFR — це вже
            # реалістичний сценарій одночасного запозичення).
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

            # Тут у п.7 backlog буде доданий виклик
            # send_telegram_message(...) — поки що навмисно НЕ додаємо,
            # щоб не забігати наперед у незалежний пункт плану.

        return borrowing
