from rest_framework import serializers
from django.utils import timezone
from .models import ImportJob, ImportRowError


class ImportRowErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportRowError
        fields = ['row_number', 'raw_data', 'error_message', 'created_at']
        read_only_fields = fields


class ImportJobSerializer(serializers.ModelSerializer):
    progress_percent = serializers.SerializerMethodField()
    errors_preview = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = ImportJob
        fields = [
            'id',
            'filename',
            'status',
            'total_rows',
            'processed_rows',
            'success_count',
            'error_count',
            'progress_percent',
            'errors_preview',
            'duration',
            'created_at',
            'started_at',
            'finished_at',
            'celery_task_id',
        ]
        read_only_fields = fields

    def get_progress_percent(self, obj) -> float:
        return obj.progress_percent

    def get_errors_preview(self, obj) -> list:
        errors = obj.errors.all()[:5]  # Preview of first 5 errors
        return ImportRowErrorSerializer(errors, many=True).data

    def get_duration(self, obj) -> str:
        if obj.started_at and obj.finished_at:
            duration = obj.finished_at - obj.started_at
            return str(duration)
        elif obj.started_at:
            duration = timezone.now() - obj.started_at
            return str(duration)
        return None


class ImportJobCreateSerializer(serializers.ModelSerializer):
    file = serializers.FileField(
        write_only=True,
        max_length=255,
        allow_empty_file=False
    )

    class Meta:
        model = ImportJob
        fields = ['file']
        read_only_fields = ['id', 'status', 'created_at']

    def validate_file(self, file):
        # Check file size
        max_size = 104857600  # 100MB
        if file.size > max_size:
            raise serializers.ValidationError(
                f"File size too large. Maximum size is {max_size // 1048576}MB"
            )

        # Check file extension
        if not file.name.lower().endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are allowed")

        # Check MIME type
        allowed_types = ['text/csv', 'text/plain', 'application/csv']
        if file.content_type not in allowed_types:
            raise serializers.ValidationError("Invalid file type")

        return file

    def create(self, validated_data):
        request = self.context.get('request')
        file = validated_data.pop('file')

        import_job = ImportJob(
            filename=file.name,
            file_path=self._save_uploaded_file(file),
            uploader=request.user if request and request.user.is_authenticated else None
        )
        import_job.save()

        return import_job

    def _save_uploaded_file(self, file) -> str:
        import os
        from django.core.files.storage import default_storage

        # Generate unique filename
        from uuid import uuid4
        filename = f"imports/{uuid4()}_{file.name}"

        # Save file
        file_path = default_storage.save(filename, file)
        return file_path


class ImportJobStatusSerializer(serializers.ModelSerializer):
    progress_percent = serializers.SerializerMethodField()
    errors_preview = serializers.SerializerMethodField()

    class Meta:
        model = ImportJob
        fields = [
            'id',
            'filename',
            'status',
            'total_rows',
            'processed_rows',
            'success_count',
            'error_count',
            'progress_percent',
            'errors_preview',
            'created_at',
            'started_at',
            'finished_at',
        ]
        read_only_fields = fields

    def get_progress_percent(self, obj) -> float:
        return obj.progress_percent

    def get_errors_preview(self, obj) -> list:
        errors = obj.errors.all()[:10]
        return ImportRowErrorSerializer(errors, many=True).data