from django.urls import path
from .views import CSVUploadView

urlpatterns = [
    path('imports/upload/', CSVUploadView.as_view(), name='csv-upload'),
]