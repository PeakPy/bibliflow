from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Book
from .serializers import (
    BookSerializer,
    BookListSerializer,
    BookDetailSerializer
)


class BookListView(generics.ListAPIView):
    serializer_class = BookListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'publication_year']
    search_fields = ['title', 'author', 'isbn']
    ordering_fields = ['title', 'author', 'publication_year', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Book.objects.all()

        # Optional: Filter by recent imports if needed
        recent_only = self.request.query_params.get('recent_only')
        if recent_only:
            from django.utils import timezone
            from datetime import timedelta
            recent_date = timezone.now() - timedelta(days=7)
            queryset = queryset.filter(created_at__gte=recent_date)

        return queryset


class BookDetailView(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookDetailSerializer


class BookSearchView(generics.ListAPIView):
    serializer_class = BookListSerializer

    def get_queryset(self):
        queryset = Book.objects.all()
        query = self.request.query_params.get('q')

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(author__icontains=query) |
                Q(isbn__icontains=query)
            )

        return queryset.order_by('-created_at')


class BookCreateView(generics.CreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookUpdateView(generics.UpdateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookDeleteView(generics.DestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer