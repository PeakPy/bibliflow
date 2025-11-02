from rest_framework import serializers
from .models import CSVImport, CSVImportRowError

class CSVImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVImport
        fields = '__all__'

class CSVImportRowErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVImportRowError
        fields = '__all__'