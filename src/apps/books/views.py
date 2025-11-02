from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Book
from .serializers import (
    BookSerializer,
    BookListSerializer,
    BookDetailSerializer
)


class BookViewSet(viewsets.ModelViewSet):
    """
    A unified ViewSet providing CRUD + search for Books.
    Avoids multiple endpoints & increases maintainability.
    """

    queryset = Book.objects.all().order_by("-created_at")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # filters
    filterset_fields = ["author", "publication_year"]
    search_fields = ["title", "author", "isbn"]
    ordering_fields = ["title", "author", "publication_year", "created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """
        Choose serializer dynamically based on action.
        """
        if self.action in ["list", "search"]:
            return BookListSerializer
        if self.action == "retrieve":
            return BookDetailSerializer
        return BookSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        if self.action == "search":
            query = self.request.query_params.get("q")
            if query:
                qs = qs.filter(
                    Q(title__icontains=query) |
                    Q(author__icontains=query) |
                    Q(isbn__icontains=query)
                )
        return qs
