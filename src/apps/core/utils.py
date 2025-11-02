import os
import magic
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


def validate_file_type(file, allowed_types):
    """Validate file type using python-magic"""
    try:
        file.seek(0)
        file_type = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)

        if file_type not in allowed_types:
            raise ValidationError(f"File type {file_type} is not allowed")

        return file_type
    except Exception as e:
        raise ValidationError(f"Could not validate file type: {e}")


def generate_unique_filename(original_filename):
    """Generate unique filename with timestamp"""
    from uuid import uuid4
    base_name, extension = os.path.splitext(original_filename)
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid4().hex[:8]
    return f"{base_name}_{timestamp}_{unique_id}{extension}"


def chunked_queryset(queryset, chunk_size=1000):
    """Split queryset into chunks for memory-efficient processing"""
    total = queryset.count()
    for start in range(0, total, chunk_size):
        end = min(start + chunk_size, total)
        yield queryset[start:end]


def safe_string(value, max_length=None):
    """Safely handle string values with length limits"""
    if value is None:
        return ""

    string_value = str(value).strip()
    if max_length and len(string_value) > max_length:
        return string_value[:max_length]

    return string_value


def calculate_processing_time(start_time, end_time=None):
    """Calculate processing time in human readable format"""
    end_time = end_time or timezone.now()
    duration = end_time - start_time

    if duration < timedelta(seconds=1):
        return f"{duration.microseconds // 1000}ms"
    elif duration < timedelta(minutes=1):
        return f"{duration.seconds}s"
    elif duration < timedelta(hours=1):
        return f"{duration.seconds // 60}m"
    else:
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        return f"{hours}h {minutes}m"


class ProgressTracker:
    """Track and report progress for long-running tasks"""

    def __init__(self, total, update_interval=100):
        self.total = total
        self.processed = 0
        self.update_interval = update_interval

    def increment(self):
        self.processed += 1

    @property
    def percentage(self):
        if self.total == 0:
            return 0
        return (self.processed / self.total) * 100

    @property
    def should_update(self):
        return self.processed % self.update_interval == 0