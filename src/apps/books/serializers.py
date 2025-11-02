from rest_framework import serializers
from .models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author',
            'isbn',
            'publication_year',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'publication_year']

    def validate_isbn(self, value):
        if not value:
            raise serializers.ValidationError("ISBN is required")
        if Book.objects.filter(isbn=value).exists():
            raise serializers.ValidationError("Book with this ISBN already exists")
        return value

    def validate_publication_year(self, value):
        if value and (value < 1000 or value > 2100):
            raise serializers.ValidationError("Publication year must be between 1000 and 2100")
        return value


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'publication_year']


class BookDetailSerializer(BookSerializer):
    class Meta(BookSerializer.Meta):
        fields = BookSerializer.Meta.fields + ['created_at', 'updated_at']