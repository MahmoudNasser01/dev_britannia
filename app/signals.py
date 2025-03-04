from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Student
from .utils import send_activation_email


@receiver(post_save, sender=Student)
def student_post_save(sender, instance, created, **kwargs):
    if instance.is_approved:
        send_activation_email(instance.user.email, instance.full_name)
