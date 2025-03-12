# models.py (keep as provided)
from django.db import models

class UploadedExam(models.Model):
    file = models.FileField(upload_to="exams/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

class GradedExam(models.Model):
    matricule = models.CharField(max_length=50, unique=True)
    score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)