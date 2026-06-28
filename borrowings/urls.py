from django.urls import path

from borrowings.views import BorrowingDetailView, BorrowingListCreateDispatchView

app_name = "borrowings"

urlpatterns = [
    path("", BorrowingListCreateDispatchView.as_view(), name="borrowing-list-create"),
    path("<int:pk>/", BorrowingDetailView.as_view(), name="borrowing-detail"),
]
