import logging
from celery import shared_task
from django.utils import timezone
from django.core.files.storage import default_storage
from .models import ImportJob
from .services.csv_importer import CSVImporter

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_csv_import(self, job_id: int) -> None:

    try:
        import_job = ImportJob.objects.get(id=job_id)

        # Check if already processed
        if import_job.status in [ImportJob.SUCCESS, ImportJob.FAILURE]:
            logger.info(f"Import job {job_id} already completed with status: {import_job.status}")
            return

        # Mark as processing
        import_job.mark_started()
        import_job.celery_task_id = self.request.id
        import_job.save()

        logger.info(f"Starting CSV import for job {job_id}")

        # Process the file
        importer = CSVImporter(import_job)
        success_count, error_count = importer.process_file()

        # Mark as completed
        import_job.mark_completed(success_count, error_count)

        logger.info(
            f"Completed CSV import for job {job_id}. "
            f"Success: {success_count}, Errors: {error_count}"
        )

    except ImportJob.DoesNotExist:
        logger.error(f"ImportJob {job_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Failed to process CSV import job {job_id}: {exc}")

        # Mark as failed
        try:
            import_job = ImportJob.objects.get(id=job_id)
            import_job.mark_failed()
        except ImportJob.DoesNotExist:
            pass

        # Retry for transient errors
        if self.request.retries < self.max_retries:
            retry_delay = self.default_retry_delay * (2 ** self.request.retries)
            raise self.retry(exc=exc, countdown=retry_delay)
        else:
            logger.error(f"Max retries exceeded for import job {job_id}")


@shared_task
def cleanup_completed_imports(days_old: int = 7) -> None:

    from django.utils import timezone
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days_old)

    old_jobs = ImportJob.objects.filter(
        status__in=[ImportJob.SUCCESS, ImportJob.FAILURE],
        created_at__lt=cutoff_date
    )

    deleted_count = 0
    for job in old_jobs:
        try:
            # Delete associated file
            if job.file_path and default_storage.exists(job.file_path):
                default_storage.delete(job.file_path)

            # Delete the job (cascades to ImportRowError)
            job.delete()
            deleted_count += 1

        except Exception as exc:
            logger.error(f"Failed to cleanup import job {job.id}: {exc}")

    logger.info(f"Cleaned up {deleted_count} old import jobs")


@shared_task
def retry_failed_import(job_id: int) -> bool:

    try:
        import_job = ImportJob.objects.get(id=job_id, status=ImportJob.FAILURE)

        # Reset job status
        import_job.status = ImportJob.PENDING
        import_job.processed_rows = 0
        import_job.error_count = 0
        import_job.success_count = 0
        import_job.started_at = None
        import_job.finished_at = None
        import_job.save()

        # Start new processing task
        process_csv_import.delay(job_id)

        logger.info(f"Retried failed import job {job_id}")
        return True

    except ImportJob.DoesNotExist:
        logger.error(f"Failed import job {job_id} not found for retry")
        return False