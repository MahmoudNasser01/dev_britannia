from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from django.contrib.auth import get_user_model
from .models import Student, Teacher, CourseLevel, ExamResult

User = get_user_model()

class ExamResultResource(resources.ModelResource):
    student = fields.Field(
        column_name='Student ID',
        attribute='student',
        widget=ForeignKeyWidget(Student, 'student_id')
    )
    teacher = fields.Field(
        column_name='Teacher',
        attribute='teacher',
        widget=ForeignKeyWidget(Teacher, 'full_name')
    )
    level = fields.Field(
        column_name='Level',
        attribute='level',
        widget=ForeignKeyWidget(CourseLevel, 'name')
    )
    date_of_creation = fields.Field(
        column_name='Date of Exam',
        attribute='date_of_creation'
    )

    class Meta:
        model = ExamResult
        fields = (
            'id',
            'date_of_creation', 'level', 'student', 'teacher', 'units_covered',
            'attendance_percentage', 'grammar', 'vocabulary', 'reading',
            'writing', 'listening', 'speaking', 'teacher_assessment', 'total_score',
            'total_percentage', 'teacher_recommendation', 'note'
        )


    def before_import_row(self, row, **kwargs):
        """Skip empty rows"""
        if not any(row.values()):  # Checks if all values in the row are empty
            raise resources.SkipRow()

        level, created = CourseLevel.objects.get_or_create(
            name=row['Level'],
            defaults={'order': 1},

        )
        # Ensure student exists
        student_user, created = User.objects.get_or_create(
            email=row['Email'],
            defaults={'is_active': True}
        )
        if created:
            student_user.set_password(row['Student ID'])
            student_user.save()

        student, created = Student.objects.get_or_create(
            user=student_user,
            defaults={
                'full_name': row['Name'],
                'student_id': row['Student ID'],
                'passport_number': row['Passport No'],
                'country': row['Nationality'],
            }
        )

        # Ensure teacher exists
        teacher_user, created = User.objects.get_or_create(
            email=f"{row['Teacher'].replace(' ', '').lower()}@school.com",
            defaults={'is_active': True}
        )
        if created:
            teacher_user.set_password("fixedpassword")
            teacher_user.save()

        teacher, created = Teacher.objects.get_or_create(
            user=teacher_user,
            defaults={'full_name': row['Teacher']}
        )

        # Assign student and teacher to row for further processing
        row['Student ID'] = student
        row['Teacher'] = teacher