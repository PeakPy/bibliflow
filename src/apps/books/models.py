from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Book(models.Model):
    title = models.CharField(max_length=512)
    author = models.CharField(max_length=256)
    isbn = models.CharField(max_length=32, unique=True)
    publication_year = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(2100)
        ]
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'books'
        indexes = [
            models.Index(fields=['isbn']),
            models.Index(fields=['author']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} by {self.author}'

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)