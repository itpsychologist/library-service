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

        return borrowing
