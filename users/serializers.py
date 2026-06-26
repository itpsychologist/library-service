from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "password", "is_staff")
        read_only_fields = ("is_staff",)
        extra_kwargs = {
            "password": {
                "write_only": True,
                "min_length": 5,
                "style": {"input_type": "password"},
            }
        }

    def create(self, validated_data):
        # create_user замість create() напряму — гарантує set_password()
        # всередині кастомного UserManager, пароль ніколи не зберігається
        # у відкритому вигляді.
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class UserSerializer(UserRegisterSerializer):
    """
    Серіалізатор для /me/. Дозволяє читати/оновлювати власний профіль.
    is_staff лишається read-only — користувач не може сам собі
    підвищити права.
    """

    class Meta(UserRegisterSerializer.Meta):
        fields = ("id", "email", "first_name", "last_name", "password", "is_staff")
