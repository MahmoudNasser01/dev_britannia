import os
from io import BytesIO

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.files import File
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from app.pdf_generate import generate_exam_result_pdf_view
from guardian.shortcuts import assign_perm


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)





class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    @property
    def is_teacher(self):
        return hasattr(self, 'teacher_profile')

    def save(self, *args, **kwargs):
        # Check if password has changed by comparing the current value with the original
        if self.pk is not None:  # Check if the object already exists in the database
            original = User.objects.get(pk=self.pk)
            if original.password != self.password:
                self.set_password(self.password)  # Only set password if it has changed
        else:
            self.set_password(self.password)  # Set password for new objects

        super().save(*args, **kwargs)


class CourseLevel(models.Model):
    MONTHS_CHOICES = [
        ('January', 'January'),
        ('February', 'February'),
        ('March', 'March'),
        ('April', 'April'),
        ('May', 'May'),
        ('June', 'June'),
        ('July', 'July'),
        ('August', 'August'),
        ('September', 'September'),
        ('October', 'October'),
        ('November', 'November'),
        ('December', 'December'),
    ]
    name = models.CharField(max_length=50, unique=True)
    order = models.IntegerField(unique=True)
    month = models.CharField(max_length=50, choices=MONTHS_CHOICES, verbose_name='Level Month')
    year = models.IntegerField(verbose_name='Level Year')

    def __str__(self):
        return f"{self.name} - {self.month}/{self.year}"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    full_name = models.CharField(max_length=255)
    student_id = models.CharField(max_length=50, unique=True)
    passport_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    country = models.CharField(max_length=100)
    level = models.ForeignKey(CourseLevel, on_delete=models.CASCADE, related_name='students', null=True, blank=True)
    phone_number = models.CharField(max_length=20)
    def __str__(self):
        return self.full_name


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    full_name = models.CharField(max_length=255)
    esignature = models.ImageField(upload_to='signatures/')

    def __str__(self):
        return self.full_name

class ManagingDirector(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='director_profile')
    full_name = models.CharField(max_length=255)
    esignature = models.ImageField(upload_to='signatures/')

    def __str__(self):
        return self.full_name



class ExamResult(models.Model):
    date_of_creation = models.DateField()
    level = models.ForeignKey(CourseLevel, on_delete=models.CASCADE, related_name='exam_results')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='exam_results')
    units_covered = models.CharField(max_length=20, verbose_name="Unites Covered e.g. (1 To 5)")
    # Assessment fields
    grammar = models.IntegerField()
    grammar_total = models.IntegerField(default=40)
    vocabulary = models.IntegerField()
    vocabulary_total = models.IntegerField(default=20)
    reading = models.IntegerField()
    reading_total = models.IntegerField(default=20)
    writing = models.IntegerField()
    writing_total = models.IntegerField(default=20)
    listening = models.IntegerField()
    listening_total = models.IntegerField(default=20)
    speaking = models.IntegerField()
    speaking_total = models.IntegerField(default=20)
    teacher_assessment = models.IntegerField()
    teacher_assessment_total = models.IntegerField(default=10)

    # Calculated fields
    total_score = models.IntegerField(null=True, blank=True)
    total_score_out_of = models.IntegerField(default=150)
    total_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Attendance and recommendation
    note = models.CharField(max_length=500)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    teacher_recommendation = models.CharField(max_length=50, choices=[('Repeat', 'Repeat'), ('Progress', 'Progress'), ('Marginal Pass', 'Marginal Pass'), ('Conditional Pass', 'Conditional Pass')])

    pdf = models.FileField(upload_to='exam_results_pdfs/', null=True, blank=True)
    class Meta:
        verbose_name = "Exam Result"
        verbose_name_plural = "Exam Results"

    def __str__(self):
        return f"{self.student.full_name} - {self.date_of_creation}"


    def save(self, *args, **kwargs):
        # Automatically calculate the total score and percentage
        self.total_score = (
                self.grammar
                + self.vocabulary
                + self.reading
                + self.writing
                + self.listening
                + self.speaking
                + self.teacher_assessment
        )
        self.total_percentage = (self.total_score / self.total_score_out_of) * 100

        # Generate the PDF content
        pdf_content = generate_exam_result_pdf_view(self)
        pdf_file_like = BytesIO(pdf_content)

        # Delete the old file if it exists
        if self.pdf:
            if os.path.isfile(self.pdf.path):
                os.remove(self.pdf.path)

        # Set a name for the PDF file and save it
        pdf_file_like.name = f"exam_result_{self.id}.pdf"
        self.pdf = File(pdf_file_like, name=pdf_file_like.name)

        # Save the instance
        super().save(*args, **kwargs)