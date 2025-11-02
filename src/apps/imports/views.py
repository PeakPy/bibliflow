from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CSVImport

class CSVUploadView(APIView):
    def post(self, request):
        # placeholder: actual file handling + task enqueue will be implemented later
        return Response({'detail': 'Upload endpoint placeholder'}, status=status.HTTP_201_CREATED)