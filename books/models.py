from django.db import models


class Book(models.Model):
    """
    Resource "Book" з технічного завдання:
    title, author, cover (HARD/SOFT), inventory (>=0), daily_fee.
    """

    class Cover(models.TextChoices):
        HARD = "HARD", "Hardcover"
        SOFT = "SOFT", "Softcover"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=4, choices=Cover.choices)
    # PositiveIntegerField дозволяє 0 (книгу можуть всю розпозичити),
    # але не дозволяє від'ємні значення на рівні БД/валідації Django.
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return f"{self.title} by {self.author}"
