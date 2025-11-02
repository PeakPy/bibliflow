from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import ImportJob, ImportRowError
from .serializers import (
    ImportJobCreateSerializer,
    ImportJobSerializer,
    ImportJobStatusSerializer,
    ImportRowErrorSerializer
)
from .tasks import process_csv_import


class ImportJobViewSet(viewsets.ModelViewSet):
    """
    Unified CSV import job controller.
    Handles: create, list, retrieve, retry & cancel.
    """

    permission_classes = [IsAuthenticated]
    queryset = ImportJob.objects.all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return ImportJobCreateSerializer
        if self.action == "retrieve":
            return ImportJobStatusSerializer
        return ImportJobSerializer

    def perform_create(self, serializer):
        job = serializer.save()
        process_csv_import.delay(job.id)
        return job

    def create(self, request, *args, **kwargs):
        job = self.perform_create(self.get_serializer(data=request.data))
        return Response(
            {
                "job_id": job.id,
                "status": job.status,
                "message": "File accepted. Processing started."
            },
            status=status.HTTP_201_CREATED
        )

    # Custom Actions for retry/cancel
    def retry(self, request, pk=None):
        job = get_object_or_404(ImportJob, id=pk, status=ImportJob.FAILURE)
        job.reset_for_retry()
        process_csv_import.delay(job.id)
        return Response({"message": "Retry queued"}, status=200)

    def cancel(self, request, pk=None):
        job = get_object_or_404(
            ImportJob,
            Q(status=ImportJob.PENDING) | Q(status=ImportJob.PROCESSING),
            id=pk
        )
        job.mark_failed()
        return Response({"message": "Job cancelled"}, status=200)


class ImportErrorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Returns all row-level import errors for a job.
    """

    serializer_class = ImportRowErrorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        job_id = self.kwargs.get("job_id")
        job = get_object_or_404(ImportJob, id=job_id)
        return job.errors.all().order_by("row_number")
