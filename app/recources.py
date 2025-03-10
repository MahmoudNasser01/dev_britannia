import re
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget, FloatWidget, DateWidget
from .models import ExamResult, Student, Teacher, CourseLevel
from import_export.results import RowResult
from datetime import datetime


class ExamResultResource(resources.ModelResource):
    student = fields.Field(
        column_name='student_id',
        attribute='student',
        widget=ForeignKeyWidget(Student, 'student_id')
    )

    teacher = fields.Field(
        column_name='teacher_id',
        attribute='teacher',
        widget=ForeignKeyWidget(Teacher, 'user__id')  # Assuming User ID is used
    )

    class Meta:
        model = ExamResult
        skip_unchanged = True
        import_id_fields = ('student', 'teacher', 'date_of_creation')  # Ensure uniqueness
        fields = ('date_of_creation', 'level', 'student', 'teacher',
                  'units_covered', 'grammar', 'vocabulary', 'reading',
                  'writing', 'listening', 'speaking', 'teacher_assessment',
                  'attendance_percentage', 'teacher_recommendation')

    def before_import_row(self, row, **kwargs):
        """ Skip row if student or teacher does not exist """
        student_id = row.get('student_id')
        passport_number = row.get('passport_number')
        teacher_id = row.get('teacher_id')

        student = Student.objects.filter(student_id=student_id).first() or \
                  Student.objects.filter(passport_number=passport_number).first()

        teacher = Teacher.objects.filter(user__id=teacher_id).first()

        if not student or not teacher:
            raise ValueError(f"Skipping row: Student or Teacher not found for Student ID: {student_id}, Teacher ID: {teacher_id}")

        row['student'] = student
        row['teacher'] = teacher


