from django.urls import path

from .views import (
    BorrowingListCreateDispatchView,
    BorrowingDetailView,
    BorrowingReturnView,
)

app_name = "borrowings"

urlpatterns = [
    path("", BorrowingListCreateDispatchView.as_view(), name="borrowing-list-create"),
    path("<int:pk>/", BorrowingDetailView.as_view(), name="borrowing-detail"),
    path(
        "<int:pk>/return/",
        BorrowingReturnView.as_view(),
        name="borrowing-return",
    ),
]
