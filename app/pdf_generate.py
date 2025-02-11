from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML
from django.core.files.base import ContentFile
import os

import os
from django.core.files.base import ContentFile



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