from django.db import models
import uuid

class CSVImport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.TextField()
    file_path = models.TextField()
    status = models.CharField(max_length=32, default='PENDING')
    total_rows = models.IntegerField(null=True, blank=True)
    processed_rows = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

class CSVImportRowError(models.Model):
    import_job = models.ForeignKey(CSVImport, on_delete=models.CASCADE, related_name='errors')
    row_number = models.IntegerField()
    raw_data = models.TextField()
    error_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)