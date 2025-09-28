# views.py

from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser
from .models import File
from .serializers import FileSerializer

class FileUploadViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all().order_by('-created_at')
    serializer_class = FileSerializer
    parser_classes = [MultiPartParser]
