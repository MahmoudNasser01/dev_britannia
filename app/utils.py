from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from email.mime.image import MIMEImage
import os


def send_activation_email(student_email, student_name):
    """
    Sends an account activation email to the student.
    :param student_email: Recipient email address
    :param student_name: Student's name
    """
    subject = "Your Account Has Been Activated! 🎉"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [student_email]

    # Load the email template and render it
    context = {"student_name": student_name}
    html_content = render_to_string("app/emails/account_activation.html", context)
    text_content = strip_tags(html_content)

    # Create email message
    email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email.attach_alternative(html_content, "text/html")

    logo_path = os.path.join(settings.BASE_DIR, "static", "square-logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img:
            logo = MIMEImage(img.read())
            logo.add_header("Content-ID", "<logo>")
            logo.add_header("Content-Disposition", "inline", filename="logo.png")
            email.attach(logo)

    email.send()
    print(f"Activation email sent to {student_email} ✅")
