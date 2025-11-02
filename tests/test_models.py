import pytest
from django.core.exceptions import ValidationError
from apps.books.models import Book
from apps.imports.models import ImportJob, ImportRowError


@pytest.mark.django_db
class TestBookModel:
    def test_create_book(self, sample_book):
        """Test basic book creation"""
        assert sample_book.title == 'Test Book'
        assert sample_book.author == 'Test Author'
        assert sample_book.isbn == '1234567890'
        assert sample_book.publication_year == 2023
        assert sample_book.created_at is not None

    def test_book_string_representation(self, sample_book):
        """Test book string representation"""
        assert str(sample_book) == 'Test Book by Test Author'

    def test_book_validation(self):
        """Test book field validation"""
        # Test valid publication year
        book = Book(
            title='Valid Book',
            author='Valid Author',
            isbn='1234567890123',
            publication_year=2020
        )
        book.full_clean()

        # Test invalid publication year
        book = Book(
            title='Invalid Book',
            author='Invalid Author',
            isbn='1234567890124',
            publication_year=3000
        )
        with pytest.raises(ValidationError):
            book.full_clean()

    def test_unique_isbn_constraint(self, sample_book):
        """Test ISBN uniqueness constraint"""
        with pytest.raises(Exception):
            Book.objects.create(
                title='Duplicate Book',
                author='Duplicate Author',
                isbn=sample_book.isbn,
                publication_year=2023
            )

    def test_book_ordering(self, user):
        """Test books are ordered by creation date descending"""
        book1 = Book.objects.create(
            title='Book 1',
            author='Author 1',
            isbn='1111111111'
        )
        book2 = Book.objects.create(
            title='Book 2',
            author='Author 2',
            isbn='2222222222'
        )

        books = Book.objects.all()
        assert books[0] == book2
        assert books[1] == book1


@pytest.mark.django_db
class TestImportJobModel:
    def test_create_import_job(self, import_job):
        """Test basic import job creation"""
        assert import_job.filename == 'test.csv'
        assert import_job.status == ImportJob.PENDING
        assert import_job.progress_percent == 0

    def test_import_job_string_representation(self, import_job):
        """Test import job string representation"""
        assert str(import_job) == 'test.csv - PENDING'

    def test_mark_started(self, import_job):
        """Test marking job as started"""
        import_job.mark_started()
        assert import_job.status == ImportJob.PROCESSING
        assert import_job.started_at is not None

    def test_mark_completed(self, import_job):
        """Test marking job as completed"""
        import_job.mark_completed(success_count=95, error_count=5)
        assert import_job.status == ImportJob.SUCCESS
        assert import_job.success_count == 95
        assert import_job.error_count == 5
        assert import_job.processed_rows == 100
        assert import_job.finished_at is not None

    def test_mark_failed(self, import_job):
        """Test marking job as failed"""
        import_job.mark_failed()
        assert import_job.status == ImportJob.FAILURE
        assert import_job.finished_at is not None

    def test_progress_percent(self, processing_import_job):
        """Test progress percentage calculation"""
        assert processing_import_job.progress_percent == 50.0

    def test_progress_percent_zero_total(self, import_job):
        """Test progress percentage with zero total rows"""
        assert import_job.progress_percent == 0

    def test_import_job_ordering(self, user):
        """Test import jobs are ordered by creation date descending"""
        job1 = ImportJob.objects.create(
            filename='job1.csv',
            file_path='/tmp/job1.csv',
            uploader=user
        )
        job2 = ImportJob.objects.create(
            filename='job2.csv',
            file_path='/tmp/job2.csv',
            uploader=user
        )

        jobs = ImportJob.objects.all()
        assert jobs[0] == job2
        assert jobs[1] == job1


@pytest.mark.django_db
class TestImportRowErrorModel:
    def test_create_import_row_error(self, import_row_errors):
        """Test import row error creation"""
        error = import_row_errors[0]
        assert error.row_number == 1
        assert error.raw_data == 'row_data_0'
        assert error.error_message == 'error_0'

    def test_import_row_error_string_representation(self, import_row_errors):
        """Test import row error string representation"""
        error = import_row_errors[0]
        assert str(error) == 'Row 1: error_0'

    def test_import_row_error_ordering(self, import_job):
        """Test import row errors are ordered by row number"""
        error1 = ImportRowError.objects.create(
            import_job=import_job,
            row_number=5,
            raw_data='data5',
            error_message='error5'
        )
        error2 = ImportRowError.objects.create(
            import_job=import_job,
            row_number=1,
            raw_data='data1',
            error_message='error1'
        )

        errors = ImportRowError.objects.all()
        assert errors[0] == error2
        assert errors[1] == error1

    def test_error_cascade_deletion(self, import_job, import_row_errors):
        """Test errors are deleted when import job is deleted"""
        error_count = ImportRowError.objects.count()
        assert error_count == 3

        import_job.delete()

        assert ImportRowError.objects.count() == 0