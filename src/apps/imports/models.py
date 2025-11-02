from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class ImportJob(models.Model):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (SUCCESS, 'Success'),
        (FAILURE, 'Failure'),
    ]

    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    uploader = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )
    total_rows = models.IntegerField(null=True, blank=True)
    processed_rows = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'import_jobs'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['celery_task_id']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.filename} - {self.status}'

    @property
    def progress_percent(self):
        if self.total_rows and self.total_rows > 0:
            return round((self.processed_rows / self.total_rows) * 100, 2)
        return 0

    def mark_started(self):
        self.status = self.PROCESSING
        self.started_at = timezone.now()
        self.save()

    def mark_completed(self, success_count, error_count):
        self.status = self.SUCCESS if error_count == 0 else self.SUCCESS
        self.success_count = success_count
        self.error_count = error_count
        self.processed_rows = success_count + error_count
        self.finished_at = timezone.now()
        self.save()

    def mark_failed(self):
        self.status = self.FAILURE
        self.finished_at = timezone.now()
        self.save()


class ImportRowError(models.Model):
    import_job = models.ForeignKey(
        ImportJob,
        on_delete=models.CASCADE,
        related_name='errors'
    )
    row_number = models.IntegerField()
    raw_data = models.TextField()
    error_message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'import_row_errors'
        indexes = [
            models.Index(fields=['import_job', 'row_number']),
        ]
        ordering = ['row_number']

    def __str__(self):
        return f'Row {self.row_number}: {self.error_message}'