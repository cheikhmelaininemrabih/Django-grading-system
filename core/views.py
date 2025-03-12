from django.shortcuts import render, redirect
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import UploadedExam, GradedExam
from .utils import extract_text_from_file, generate_correct_answers, grade_exam
import os
import openpyxl
import re

# ✅ Upload Page
def upload_page(request):
    """Render the file upload page."""
    return render(request, "core/upload.html")


# ✅ File Upload Handling
@api_view(["POST"])
def upload_exams(request):
    """Upload new exam files and delete old ones to prevent duplicates."""

    # ✅ Delete all previous uploads
    UploadedExam.objects.all().delete()
    
    uploaded_files = request.FILES.getlist("files")
    
    # ✅ Save new files
    for file in uploaded_files:
        UploadedExam.objects.create(file=file)

    return render(request, "core/upload.html", {"message": "Files uploaded successfully!"})


def results_page(request):
    """Grade student submissions, show results in table, and store for export."""

    # ✅ Find the exam file
    exam_files = UploadedExam.objects.filter(file__icontains='exam')
    
    if not exam_files.exists():
        return render(request, "core/results.html", {"error": "No exam file found!"})

    # ✅ Extract exam text
    exam_upload = exam_files.first()
    exam_text = extract_text_from_file(exam_upload.file.path)

    correct_answers = generate_correct_answers(exam_text)
    results = []

    # ✅ Process student answer files **ONLY those containing '2'**
    student_uploads = UploadedExam.objects.filter(file__regex=r".*2.*\.(pdf|py|cpp|sql|txt)$")

    for upload in student_uploads:
        try:
            matricule = os.path.splitext(os.path.basename(upload.file.name))[0]

            # ✅ Extract only numeric matricule (Ensures it's 5 digits & starts with 2)
            match = re.search(r"2\d{4}", matricule)  # Find the first "2" followed by exactly 4 more digits
  # Looks for 5-digit numbers starting with "2"
            if not match:
                print(f"❌ Skipping invalid matricule: {matricule}")
                continue  # Skip if no valid matricule found

            numeric_matricule = match.group()

            student_text = extract_text_from_file(upload.file.path)

            if not student_text.strip():
                continue  # Skip empty files

            score = grade_exam(correct_answers, student_text, exam_text)

            # ✅ Save to database
            GradedExam.objects.update_or_create(
                matricule=numeric_matricule,
                defaults={"score": score}
            )
            results.append({"Matricule": numeric_matricule, "Score": round(score, 1)})

        except Exception as e:
            print(f"❌ Error processing {upload.file.name}: {str(e)}")

    # ✅ Store results in session for exporting
    request.session["filtered_results"] = results

    # ✅ Pass results to the template
    return render(request, "core/results.html", {"results": results})
# ✅ Export Grading Results as Excel
def export_filtered_grades_excel(request):
    """Generate an Excel file with only the displayed student results (filtered)."""

    # ✅ Get the filtered results from session (or modify based on your logic)
    results = request.session.get("filtered_results", [])  # Retrieve results stored in session

    if not results:
        return HttpResponse("❌ No results found to export!", status=400)

    # ✅ Create a new Excel workbook & sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Filtered Grading Results"

    # ✅ Add headers
    ws.append(["Matricule", "Grade"])

    # ✅ Filter only valid numeric matricules and append them to the Excel sheet
    for result in results:
        matricule = str(result["Matricule"])
        
        # ✅ Extract only numbers from Matricule
        numeric_matricule = "".join(re.findall(r"\d+", matricule))
        
        if numeric_matricule:  # ✅ Ensure it's not empty
            ws.append([numeric_matricule, result["Score"]])

    # ✅ Prepare HTTP response
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="filtered_grading_results.xlsx"'

    # ✅ Save workbook to response
    wb.save(response)
    return response