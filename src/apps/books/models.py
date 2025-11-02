from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=512)
    author = models.CharField(max_length=256)
    isbn = models.CharField(max_length=32, unique=True)
    publication_year = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f\"{self.title} — {self.author}\"