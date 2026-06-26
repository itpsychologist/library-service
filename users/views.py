from rest_framework import generics, permissions

from users.serializers import UserRegisterSerializer, UserSerializer


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = (permissions.AllowAny,)  # реєстрація доступна всім


class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        # /me/ завжди повертає профіль поточного користувача з токена,
        # а не за id з URL — це і відрізняє "мій профіль" від звичайного
        # detail-ендпоінту.
        return self.request.user
