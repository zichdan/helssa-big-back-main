# models.py

from django.db import models

class File(models.Model):
    file = models.FileField(upload_to='files/')  # آپلود در MinIO مسیر agents/
    file_type = models.CharField(max_length=20, choices=[('mp3', 'mp3'), ('wav', 'wav')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_type} @ {self.created_at}"
