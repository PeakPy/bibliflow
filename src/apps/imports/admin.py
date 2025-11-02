from django.contrib import admin
from .models import ImportJob, ImportRowError


class ImportRowErrorInline(admin.TabularInline):
    model = ImportRowError
    extra = 0
    readonly_fields = ['row_number', 'raw_data', 'error_message', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = [
        'filename',
        'status',
        'uploader',
        'processed_rows',
        'success_count',
        'error_count',
        'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['filename', 'celery_task_id']
    readonly_fields = [
        'filename',
        'file_path',
        'status',
        'processed_rows',
        'success_count',
        'error_count',
        'celery_task_id',
        'created_at',
        'started_at',
        'finished_at',
        'progress_percent'
    ]
    inlines = [ImportRowErrorInline]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Job Information', {
            'fields': (
                'filename',
                'file_path',
                'uploader',
                'status',
                'celery_task_id'
            )
        }),
        ('Progress', {
            'fields': (
                'total_rows',
                'processed_rows',
                'success_count',
                'error_count',
                'progress_percent'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'started_at',
                'finished_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def progress_percent(self, obj):
        return f"{obj.progress_percent}%"
    progress_percent.short_description = 'Progress'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ImportRowError)
class ImportRowErrorAdmin(admin.ModelAdmin):
    list_display = [
        'import_job',
        'row_number',
        'error_message',
        'created_at'
    ]
    list_filter = ['import_job', 'created_at']
    search_fields = ['error_message', 'raw_data']
    readonly_fields = [
        'import_job',
        'row_number',
        'raw_data',
        'error_message',
        'created_at'
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False