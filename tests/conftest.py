import pytest
import tempfile
import csv
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.books.models import Book
from apps.imports.models import ImportJob

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def staff_user():
    return User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='testpass123',
        is_staff=True
    )


@pytest.fixture
def sample_book():
    return Book.objects.create(
        title='Test Book',
        author='Test Author',
        isbn='1234567890',
        publication_year=2023
    )


@pytest.fixture
def sample_csv_file():
    """Create a sample CSV file for testing"""
    csv_content = """title,author,isbn,publication_year
Book One,Author One,1111111111,2020
Book Two,Author Two,2222222222,2021
Book Three,Author Three,3333333333,2022"""

    return SimpleUploadedFile(
        "test_books.csv",
        csv_content.encode('utf-8'),
        content_type="text/csv"
    )


@pytest.fixture
def invalid_csv_file():
    """Create an invalid CSV file for testing"""
    csv_content = """title,author,isbn
Book One,Author One
Book Two,Author Two,2222222222,invalid_year"""

    return SimpleUploadedFile(
        "invalid_books.csv",
        csv_content.encode('utf-8'),
        content_type="text/csv"
    )


@pytest.fixture
def import_job(user):
    return ImportJob.objects.create(
        filename='test.csv',
        file_path='/tmp/test.csv',
        uploader=user,
        status=ImportJob.PENDING
    )


@pytest.fixture
def processing_import_job(user):
    return ImportJob.objects.create(
        filename='processing.csv',
        file_path='/tmp/processing.csv',
        uploader=user,
        status=ImportJob.PROCESSING,
        total_rows=100,
        processed_rows=50
    )


@pytest.fixture
def completed_import_job(user):
    return ImportJob.objects.create(
        filename='completed.csv',
        file_path='/tmp/completed.csv',
        uploader=user,
        status=ImportJob.SUCCESS,
        total_rows=100,
        processed_rows=100,
        success_count=95,
        error_count=5
    )


@pytest.fixture
def failed_import_job(user):
    return ImportJob.objects.create(
        filename='failed.csv',
        file_path='/tmp/failed.csv',
        uploader=user,
        status=ImportJob.FAILURE
    )


@pytest.fixture
def import_row_errors(import_job):
    errors = []
    for i in range(3):
        errors.append(
            ImportRowError.objects.create(
                import_job=import_job,
                row_number=i + 1,
                raw_data=f"row_data_{i}",
                error_message=f"error_{i}"
            )
        )
    return errors


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def staff_client(api_client, staff_user):
    api_client.force_authenticate(user=staff_user)
    return api_client


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file on disk"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['title', 'author', 'isbn', 'publication_year'])
        writer.writerow(['Temp Book 1', 'Temp Author 1', '4444444444', '2020'])
        writer.writerow(['Temp Book 2', 'Temp Author 2', '5555555555', '2021'])
        temp_path = f.name

    yield temp_path

    # Cleanup
    import os
    os.unlink(temp_path)