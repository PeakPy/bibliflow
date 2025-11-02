import pytest
from django.urls import reverse
from rest_framework import status
from apps.books.models import Book
from apps.imports.models import ImportJob, ImportRowError


@pytest.mark.django_db
class TestBookAPI:
    def test_list_books(self, authenticated_client, sample_book):
        """Test listing books"""
        url = reverse('book-list')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == sample_book.title

    def test_search_books(self, authenticated_client, sample_book):
        """Test book search functionality"""
        url = reverse('book-search')
        response = authenticated_client.get(url, {'q': 'Test'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['title'] == sample_book.title

    def test_create_book(self, authenticated_client):
        """Test creating a new book"""
        url = reverse('book-create')
        data = {
            'title': 'New Book',
            'author': 'New Author',
            'isbn': '9999999999',
            'publication_year': 2024
        }
        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Book.objects.filter(isbn='9999999999').exists()

    def test_book_detail(self, authenticated_client, sample_book):
        """Test retrieving book details"""
        url = reverse('book-detail', kwargs={'pk': sample_book.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == sample_book.title

    def test_update_book(self, staff_client, sample_book):
        """Test updating book details"""
        url = reverse('book-update', kwargs={'pk': sample_book.id})
        data = {'title': 'Updated Book Title'}
        response = staff_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        sample_book.refresh_from_db()
        assert sample_book.title == 'Updated Book Title'

    def test_delete_book(self, staff_client, sample_book):
        """Test deleting a book"""
        url = reverse('book-delete', kwargs={'pk': sample_book.id})
        response = staff_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Book.objects.filter(id=sample_book.id).exists()


@pytest.mark.django_db
class TestImportAPI:
    def test_create_import_job(self, authenticated_client, sample_csv_file):
        """Test creating a new import job"""
        url = reverse('import-create')
        response = authenticated_client.post(url, {'file': sample_csv_file})

        assert response.status_code == status.HTTP_201_CREATED
        assert 'job_id' in response.data
        assert 'task_id' in response.data
        assert response.data['status'] == 'PENDING'

        # Verify job was created
        job_id = response.data['job_id']
        assert ImportJob.objects.filter(id=job_id).exists()

    def test_create_import_invalid_file(self, authenticated_client):
        """Test import creation with invalid file"""
        url = reverse('import-create')

        # Test with non-CSV file
        from django.core.files.uploadedfile import SimpleUploadedFile
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"invalid content",
            content_type="text/plain"
        )

        response = authenticated_client.post(url, {'file': invalid_file})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_import_jobs(self, authenticated_client, import_job):
        """Test listing import jobs"""
        url = reverse('import-list')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['filename'] == import_job.filename

    def test_list_import_jobs_filtered(self, authenticated_client, import_job, completed_import_job):
        """Test listing import jobs with status filter"""
        url = reverse('import-list')
        response = authenticated_client.get(url, {'status': 'PENDING'})

        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['status'] == 'PENDING'

    def test_import_job_status(self, authenticated_client, import_job):
        """Test retrieving import job status"""
        url = reverse('import-status', kwargs={'pk': import_job.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == import_job.id
        assert response.data['status'] == import_job.status
        assert 'progress_percent' in response.data

    def test_import_job_errors(self, authenticated_client, import_job, import_row_errors):
        """Test retrieving import job errors"""
        url = reverse('import-errors', kwargs={'pk': import_job.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        assert response.data[0]['row_number'] == 1

    def test_retry_failed_import(self, authenticated_client, failed_import_job):
        """Test retrying a failed import"""
        url = reverse('import-retry', kwargs={'pk': failed_import_job.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Import job queued for retry'

        failed_import_job.refresh_from_db()
        assert failed_import_job.status == 'PENDING'

    def test_cancel_import_job(self, authenticated_client, import_job):
        """Test canceling an import job"""
        url = reverse('import-cancel', kwargs={'pk': import_job.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK

        import_job.refresh_from_db()
        assert import_job.status == 'FAILURE'

    def test_cancel_completed_job(self, authenticated_client, completed_import_job):
        """Test canceling already completed job should fail"""
        url = reverse('import-cancel', kwargs={'pk': completed_import_job.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAPIPermissions:
    def test_unauthenticated_access(self, api_client):
        """Test unauthenticated access to protected endpoints"""
        urls = [
            reverse('book-list'),
            reverse('import-create'),
            reverse('import-list'),
        ]

        for url in urls:
            response = api_client.get(url)
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_cannot_access_others_imports(self, user, authenticated_client):
        """Test users can only see their own imports"""
        # Create import job with different user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )

        other_job = ImportJob.objects.create(
            filename='other.csv',
            file_path='/tmp/other.csv',
            uploader=other_user
        )

        url = reverse('import-status', kwargs={'pk': other_job.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_staff_can_access_all_imports(self, staff_client, import_job):
        """Test staff can access all imports"""
        url = reverse('import-status', kwargs={'pk': import_job.id})
        response = staff_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_regular_user_cannot_delete_books(self, authenticated_client, sample_book):
        """Test regular users cannot delete books"""
        url = reverse('book-delete', kwargs={'pk': sample_book.id})
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAPIPaginationAndFiltering:
    def test_book_list_pagination(self, authenticated_client):
        """Test book list pagination"""
        # Create multiple books
        for i in range(15):
            Book.objects.create(
                title=f'Book {i}',
                author=f'Author {i}',
                isbn=f'000000000{i:02d}'
            )

        url = reverse('book-list')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 10  # Default page size
        assert 'next' in response.data
        assert 'previous' in response.data

    def test_book_ordering(self, authenticated_client):
        """Test book ordering"""
        Book.objects.create(title='Book A', author='Author A', isbn='1111111111')
        Book.objects.create(title='Book B', author='Author B', isbn='2222222222')

        url = reverse('book-list')
        response = authenticated_client.get(url, {'ordering': 'title'})

        assert response.status_code == status.HTTP_200_OK
        titles = [book['title'] for book in response.data['results']]
        assert titles == ['Book A', 'Book B']

    def test_book_search(self, authenticated_client):
        """Test book search across multiple fields"""
        Book.objects.create(title='Python Guide', author='John Doe', isbn='1111111111')
        Book.objects.create(title='Django Book', author='Jane Smith', isbn='2222222222')

        url = reverse('book-search')
        response = authenticated_client.get(url, {'q': 'Python'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['title'] == 'Python Guide'