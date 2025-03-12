from django.urls import path
from .views import upload_page, upload_exams, results_page, export_filtered_grades_excel

urlpatterns = [
    path('', upload_page, name="upload_page"),
    path('upload/', upload_exams, name="upload_exams"),
    path('results/', results_page, name="results_page"),
    path('export_excel/', export_filtered_grades_excel, name="export_filtered_grades_excel"),
]
