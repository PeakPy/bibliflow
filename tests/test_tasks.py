import pytest
from unittest.mock import patch, MagicMock
from django.core.files.storage import Storage
from apps.imports.models import ImportJob, ImportRowError
from apps.imports.tasks import (
    process_csv_import,
    cleanup_completed_imports,
    retry_failed_import
)
from apps.imports.services.csv_importer import CSVImporter


@pytest.mark.django_db
class TestProcessCSVImportTask:
    def test_successful_import_processing(self, import_job, temp_csv_file):
        """Test successful CSV import processing"""
        import_job.file_path = temp_csv_file
        import_job.save()

        with patch.object(CSVImporter, 'process_file') as mock_process:
            mock_process.return_value = (2, 0)

            process_csv_import(import_job.id)

            import_job.refresh_from_db()
            assert import_job.status == ImportJob.SUCCESS
            assert import_job.success_count == 2
            assert import_job.error_count == 0
            mock_process.assert_called_once()

    def test_import_job_not_found(self):
        """Test handling of non-existent import job"""
        with pytest.raises(ImportJob.DoesNotExist):
            process_csv_import(99999)

    def test_already_completed_job(self, completed_import_job):
        """Test skipping already completed job"""
        with patch.object(CSVImporter, 'process_file') as mock_process:
            process_csv_import(completed_import_job.id)
            mock_process.assert_not_called()

    def test_import_with_errors(self, import_job, temp_csv_file):
        """Test import with some row errors"""
        import_job.file_path = temp_csv_file
        import_job.save()

        with patch.object(CSVImporter, 'process_file') as mock_process:
            mock_process.return_value = (1, 2)

            process_csv_import(import_job.id)

            import_job.refresh_from_db()
            assert import_job.status == ImportJob.SUCCESS
            assert import_job.success_count == 1
            assert import_job.error_count == 2

    def test_import_processing_failure(self, import_job):
        """Test import processing failure"""
        import_job.file_path = '/nonexistent/file.csv'
        import_job.save()

        process_csv_import(import_job.id)

        import_job.refresh_from_db()
        assert import_job.status == ImportJob.FAILURE

    def test_retry_on_transient_error(self, import_job):
        """Test retry mechanism on transient errors"""
        with patch.object(CSVImporter, 'process_file') as mock_process:
            mock_process.side_effect = Exception("Transient error")

            # First call should raise and schedule retry
            with pytest.raises(Exception):
                process_csv_import(import_job.id, max_retries=3)

    def test_mark_failed_after_max_retries(self, import_job):
        """Test job marked as failed after max retries"""
        task = process_csv_import
        task.max_retries = 3

        with patch.object(CSVImporter, 'process_file') as mock_process:
            mock_process.side_effect = Exception("Persistent error")

            # Simulate max retries exceeded
            with patch.object(task, 'retry') as mock_retry:
                mock_retry.side_effect = Exception("Max retries exceeded")

                try:
                    process_csv_import(import_job.id)
                except Exception:
                    pass

                import_job.refresh_from_db()
                assert import_job.status == ImportJob.FAILURE


@pytest.mark.django_db
class TestCleanupCompletedImportsTask:
    def test_cleanup_old_completed_jobs(self, completed_import_job, failed_import_job):
        """Test cleanup of old completed and failed jobs"""
        # Make jobs old by setting created_at to past
        from django.utils import timezone
        from datetime import timedelta

        old_date = timezone.now() - timedelta(days=10)
        ImportJob.objects.filter(id__in=[completed_import_job.id, failed_import_job.id]).update(created_at=old_date)

        with patch.object(Storage, 'delete') as mock_delete:
            with patch.object(Storage, 'exists', return_value=True):
                cleanup_completed_imports(days_old=7)

                # Verify jobs are deleted
                assert not ImportJob.objects.filter(id=completed_import_job.id).exists()
                assert not ImportJob.objects.filter(id=failed_import_job.id).exists()
                assert mock_delete.call_count == 2

    def test_cleanup_skips_recent_jobs(self, completed_import_job):
        """Test cleanup skips recently created jobs"""
        job_count_before = ImportJob.objects.count()

        cleanup_completed_imports(days_old=30)

        job_count_after = ImportJob.objects.count()
        assert job_count_before == job_count_after

    def test_cleanup_handles_missing_files(self, completed_import_job):
        """Test cleanup handles missing files gracefully"""
        # Make job old
        from django.utils import timezone
        from datetime import timedelta
        old_date = timezone.now() - timedelta(days=10)
        completed_import_job.created_at = old_date
        completed_import_job.save()

        with patch.object(Storage, 'exists', return_value=False):
            with patch.object(Storage, 'delete') as mock_delete:
                cleanup_completed_imports(days_old=7)

                # Job should still be deleted even if file doesn't exist
                assert not ImportJob.objects.filter(id=completed_import_job.id).exists()
                mock_delete.assert_not_called()

    def test_cleanup_preserves_processing_jobs(self, processing_import_job):
        """Test cleanup preserves jobs that are still processing"""
        # Make job old but still processing
        from django.utils import timezone
        from datetime import timedelta
        old_date = timezone.now() - timedelta(days=10)
        processing_import_job.created_at = old_date
        processing_import_job.save()

        job_count_before = ImportJob.objects.count()
        cleanup_completed_imports(days_old=7)
        job_count_after = ImportJob.objects.count()

        assert job_count_before == job_count_after
        assert ImportJob.objects.filter(id=processing_import_job.id).exists()


@pytest.mark.django_db
class TestRetryFailedImportTask:
    def test_successful_retry(self, failed_import_job):
        """Test successful retry of failed import"""
        with patch('apps.imports.tasks.process_csv_import.delay') as mock_delay:
            result = retry_failed_import(failed_import_job.id)

            failed_import_job.refresh_from_db()
            assert result is True
            assert failed_import_job.status == ImportJob.PENDING
            assert failed_import_job.processed_rows == 0
            assert failed_import_job.error_count == 0
            mock_delay.assert_called_once_with(failed_import_job.id)

    def test_retry_non_existent_job(self):
        """Test retry of non-existent job"""
        result = retry_failed_import(99999)
        assert result is False

    def test_retry_non_failed_job(self, completed_import_job):
        """Test retry of job that isn't failed"""
        result = retry_failed_import(completed_import_job.id)
        assert result is False

    def test_retry_resets_job_metrics(self, failed_import_job):
        """Test retry resets job metrics properly"""
        # Set some metrics to simulate previous failure
        failed_import_job.processed_rows = 50
        failed_import_job.error_count = 10
        failed_import_job.success_count = 40
        failed_import_job.save()

        retry_failed_import(failed_import_job.id)

        failed_import_job.refresh_from_db()
        assert failed_import_job.processed_rows == 0
        assert failed_import_job.error_count == 0
        assert failed_import_job.success_count == 0
        assert failed_import_job.started_at is None
        assert failed_import_job.finished_at is None