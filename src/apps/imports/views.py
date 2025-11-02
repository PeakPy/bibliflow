from rest_framework import generics, status
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


class ImportJobCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ImportJobCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        import_job = serializer.save()

        # Start async processing
        process_csv_import.delay(import_job.id)

        response_serializer = ImportJobSerializer(import_job)
        return Response(
            {
                'job_id': import_job.id,
                'task_id': import_job.celery_task_id,
                'status': import_job.status,
                'message': 'File accepted. Processing started.'
            },
            status=status.HTTP_201_CREATED
        )


class ImportJobListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ImportJobSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = ImportJob.objects.all()

        # Filter by user if not staff
        if not user.is_staff:
            queryset = queryset.filter(uploader=user)

        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('-created_at')


class ImportJobStatusView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ImportJobStatusSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = ImportJob.objects.all()

        if not user.is_staff:
            queryset = queryset.filter(uploader=user)

        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        response_data = serializer.data
        response_data.update({
            'message': self._get_status_message(instance.status)
        })

        return Response(response_data)

    def _get_status_message(self, status):
        messages = {
            ImportJob.PENDING: 'Import is queued for processing',
            ImportJob.PROCESSING: 'Import is currently being processed',
            ImportJob.SUCCESS: 'Import completed successfully',
            ImportJob.FAILURE: 'Import failed to complete',
        }
        return messages.get(status, 'Unknown status')


class ImportJobErrorsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ImportRowErrorSerializer

    def get_queryset(self):
        job_id = self.kwargs['pk']
        user = self.request.user

        # Verify user has access to this job
        queryset = ImportJob.objects.filter(id=job_id)
        if not user.is_staff:
            queryset = queryset.filter(uploader=user)

        job = get_object_or_404(queryset)
        return job.errors.all().order_by('row_number')


class ImportJobRetryView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        queryset = ImportJob.objects.filter(id=pk, status=ImportJob.FAILURE)

        if not user.is_staff:
            queryset = queryset.filter(uploader=user)

        import_job = get_object_or_404(queryset)

        # Reset and retry
        import_job.status = ImportJob.PENDING
        import_job.processed_rows = 0
        import_job.error_count = 0
        import_job.success_count = 0
        import_job.started_at = None
        import_job.finished_at = None
        import_job.save()

        process_csv_import.delay(import_job.id)

        return Response({
            'job_id': import_job.id,
            'message': 'Import job queued for retry'
        }, status=status.HTTP_200_OK)


class ImportJobCancelView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        queryset = ImportJob.objects.filter(
            Q(status=ImportJob.PENDING) | Q(status=ImportJob.PROCESSING)
        ).filter(id=pk)

        if not user.is_staff:
            queryset = queryset.filter(uploader=user)

        import_job = get_object_or_404(queryset)

        # Note: Celery task will continue running but job marked as failed
        import_job.mark_failed()

        return Response({
            'job_id': import_job.id,
            'message': 'Import job cancelled'
        }, status=status.HTTP_200_OK)