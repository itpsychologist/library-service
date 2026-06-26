from django.contrib.auth.models import AbstractUser
from django.db import models

from users.managers import UserManager


class User(AbstractUser):
    """
    Прибираємо `username` повністю — авторизуємось виключно за email.
    is_staff успадковується від AbstractUser і використовується
    далі для permissions у Books/Borrowings (admin-only дії).
    """

    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email вже є USERNAME_FIELD, дублювати не треба

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"