import csv
import logging
from typing import Dict, List, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.books.models import Book
from apps.imports.models import ImportJob, ImportRowError

logger = logging.getLogger(__name__)


class CSVImporter:
    def __init__(self, import_job: ImportJob):
        self.import_job = import_job
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0

    def process_file(self) -> Tuple[int, int]:
        try:
            with open(self.import_job.file_path, 'r', encoding='utf-8') as file:
                # Detect and skip header
                sample = file.read(1024)
                file.seek(0)
                has_header = csv.Sniffer().has_header(sample)

                reader = csv.DictReader(file) if has_header else csv.reader(file)

                for row_number, row in enumerate(reader, start=2 if has_header else 1):
                    self._process_row(row_number, row)

                    # Periodic progress update
                    if self.processed_count % 100 == 0:
                        self._update_progress()

                # Final progress update
                self._update_progress()

        except Exception as e:
            logger.error(f"Failed to process CSV file: {e}")
            raise

        return self.success_count, self.error_count

    def _process_row(self, row_number: int, row_data) -> None:
        try:
            if isinstance(row_data, dict):
                book_data = self._validate_row_data(row_data)
            else:
                book_data = self._parse_list_row(row_data)

            self._create_book(book_data)
            self.success_count += 1

        except ValidationError as e:
            self._handle_row_error(row_number, str(row_data), str(e))
        except Exception as e:
            self._handle_row_error(row_number, str(row_data), f"Unexpected error: {e}")

        self.processed_count += 1

    def _validate_row_data(self, row_data: Dict) -> Dict:
        required_fields = ['title', 'author', 'isbn']

        for field in required_fields:
            if not row_data.get(field):
                raise ValidationError(f"Missing required field: {field}")

        return {
            'title': row_data['title'].strip(),
            'author': row_data['author'].strip(),
            'isbn': row_data['isbn'].strip(),
            'publication_year': self._parse_publication_year(row_data.get('publication_year'))
        }

    def _parse_list_row(self, row_data: List) -> Dict:
        if len(row_data) < 3:
            raise ValidationError("Insufficient columns in row")

        return {
            'title': row_data[0].strip(),
            'author': row_data[1].strip(),
            'isbn': row_data[2].strip(),
            'publication_year': self._parse_publication_year(row_data[3] if len(row_data) > 3 else None)
        }

    def _parse_publication_year(self, year_str: str) -> int:
        if not year_str:
            return None

        try:
            year = int(year_str.strip())
            if year < 1000 or year > 2100:
                raise ValidationError(f"Invalid publication year: {year}")
            return year
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid publication year format: {year_str}")

    def _create_book(self, book_data: Dict) -> None:
        try:
            with transaction.atomic():
                Book.objects.create(**book_data)
        except Exception as e:
            raise ValidationError(f"Database error: {e}")

    def _handle_row_error(self, row_number: int, raw_data: str, error_message: str) -> None:
        ImportRowError.objects.create(
            import_job=self.import_job,
            row_number=row_number,
            raw_data=raw_data[:1000],  # Limit length
            error_message=error_message
        )
        self.error_count += 1
        logger.warning(f"Row {row_number} error: {error_message}")

    def _update_progress(self) -> None:
        self.import_job.processed_rows = self.processed_count
        self.import_job.error_count = self.error_count
        self.import_job.save(update_fields=['processed_rows', 'error_count'])