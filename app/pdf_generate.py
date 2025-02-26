from io import BytesIO

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML
from PyPDF2 import PdfMerger



def generate_exam_result_pdf_view(exam_result):
    from app.models import ManagingDirector

    try:
        logo_path = settings.BASE_DIR / 'static' / 'square-logo.png'
        teacher_signature_path = settings.BASE_DIR / exam_result.teacher.esignature.path
        manager_signature_path = settings.BASE_DIR / ManagingDirector.objects.first().esignature.path
        # Render the HTML template with context
        html_content = render_to_string('app/exam_result_pdf.html', {
            'exam_result': exam_result,
            'logo_path': logo_path,
            'teacher_signature_path': teacher_signature_path,
            'manager_signature_path': manager_signature_path
        })

        # Convert the HTML content to a PDF using WeasyPrint
        pdf = HTML(string=str(html_content), base_url=str(settings.BASE_DIR)).write_pdf()


        return pdf

    except Exception as e:
        raise Exception(f"Failed to generate PDF: {str(e)}")



def generate_all_exam_results_pdf(student):
    from app.models import ExamResult

    try:
        # Retrieve all exam results for the student
        exam_results = ExamResult.objects.filter(student=student)



        # Initialize a PdfMerger object
        pdf_merger = PdfMerger()

        # Generate a PDF for each exam result and add it to the merger
        for exam_result in exam_results:
            pdf_content = generate_exam_result_pdf_view(exam_result)
            pdf_merger.append(BytesIO(pdf_content))

        # Create a BytesIO object to hold the final PDF
        final_pdf = BytesIO()

        # Write the merged PDF to the BytesIO object
        pdf_merger.write(final_pdf)
        pdf_merger.close()

        # Return the final PDF content
        final_pdf.seek(0)
        return final_pdf.getvalue()

    except Exception as e:
        raise Exception(f"Failed to generate combined PDF: {str(e)}")