from rest_framework.viewsets import ModelViewSet

from books.models import Book
from books.permissions import IsAdminOrReadOnly
from books.serializers import BookSerializer


class BookViewSet(ModelViewSet):
    """
    POST    /api/books/        - додати нову книгу (тільки staff)
    GET     /api/books/        - список книг (всім, включно з анонімними)
    GET     /api/books/<id>/   - деталі книги (всім)
    PUT/PATCH /api/books/<id>/ - оновити книгу, в т.ч. inventory (тільки staff)
    DELETE  /api/books/<id>/   - видалити книгу (тільки staff)
    """

    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = (IsAdminOrReadOnly,)
