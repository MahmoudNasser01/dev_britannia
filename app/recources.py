import re
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget, FloatWidget, DateWidget
from .models import ExamResult, Student, Teacher, CourseLevel
from import_export.results import RowResult
from datetime import datetime


class ExamResultResource(resources.ModelResource):
    student = fields.Field(
        column_name="Name",
        attribute="student",
        widget=ForeignKeyWidget(Student, "full_name"),
    )
    teacher = fields.Field(
        column_name="Teacher",
        attribute="teacher",
        widget=ForeignKeyWidget(Teacher, "full_name"),
    )
    level = fields.Field(
        column_name="Level",
        attribute="level",
        widget=ForeignKeyWidget(CourseLevel, "name"),
    )

    date_of_creation = fields.Field(
        column_name="Date of Exam",
        attribute="date_of_creation",
        widget=DateWidget(format="%Y-%m-%d"),
    )
    units_covered = fields.Field(column_name="Units Covered", attribute="units_covered")
    attendance_percentage = fields.Field(
        column_name="Attendance%", attribute="attendance_percentage"
    )

    teacher_recommendation = fields.Field(
        column_name="Teacher Recommendation", attribute="teacher_recommendation"
    )
    teacher_notes = fields.Field(column_name="Teacher Notes", attribute="note")

    # Define assessment fields dynamically
    assessment_fields = {
        "Grammar": "grammar",
        "Vocabulary": "vocabulary",
        "Reading": "reading",
        "Writing": "writing",
        "Listening": "listening",
        "Speaking": "speaking",
        "Teacher Assesment": "teacher_assessment",
    }

    # Dynamically create field mappings
    for column_name, attribute in assessment_fields.items():
        locals()[f"{attribute}_score"] = fields.Field(
            column_name=column_name, attribute=attribute, widget=FloatWidget()
        )
        locals()[f"{attribute}_total"] = fields.Field(
            column_name=f"{column_name}/Total",
            attribute=f"{attribute}_total",
            widget=FloatWidget(),
        )

    def before_save_instance(self, instance, row, **kwargs):
        """Ensure all assessment fields are initialized to 0 if missing."""
        if not instance.date_of_creation:
            instance.date_of_creation = datetime.today().date()

        if instance.teacher_recommendation:
            instance.teacher_recommendation = instance.teacher_recommendation.title()

    def before_import_row(self, row, row_number=None, **kwargs):
        """
        Validates foreign key relationships before importing.
        Returns row instead of None to allow processing.
        """
        # Normalize and clean assessment fields before processing.
        for column_name, attribute in self.assessment_fields.items():
            score_key = next(
                (
                    key
                    for key in row.keys()
                    if re.match(rf"^{column_name}", key, re.IGNORECASE)
                ),
                None,
            )

            if score_key:
                total_match = re.search(r"/(\d+)$", score_key)
                total_value = float(total_match.group(1)) if total_match else 0.0

                # Assign cleaned score and total to the correct attributes
                score_value = str(row.get(score_key, "")).strip()

                try:
                    row[attribute] = float(score_value)
                except ValueError:
                    row[attribute] = 0.0

                row[f"{column_name}/Total"] = total_value

                row[f"{column_name}"] = row[attribute]
                row[f"{attribute}_total"] = total_value

        # Validate Student
        passport_number = str(row.get("Passport No", "")).strip()
        student = Student.objects.filter(
            passport_number__iexact=passport_number
        ).first()
        if not student:
            print(
                f"Skipping row {row_number}: No student found with Passport No '{passport_number}'"
            )
            return None

        # Validate Teacher
        teacher_name = str(row.get("Teacher", "")).strip()
        teacher_id = str(row.get("Teacher ID", "")).strip() or None

        teacher = Teacher.objects.filter(full_name__iexact=teacher_name).first()
        if not teacher and teacher_id:
            teacher = Teacher.objects.filter(id=teacher_id).first()

        if not teacher:
            print(
                f"Skipping row {row_number}: No teacher found with name '{teacher_name}' or ID '{teacher_id}'"
            )
            return None

        # Validate Course Level
        level_name = str(row.get("Level", "")).strip()
        level = CourseLevel.objects.filter(name__iexact=level_name).first()
        if not level:
            print(
                f"Skipping row {row_number}: No course level found with name '{level_name}'"
            )
            return None

        # Normalize missing values
        for field in ["units_covered", "attendance%", "teacher_recommendation"]:
            row[field] = row.get(field, "").strip() or None

        return row

    def import_row(self, row, instance_loader, **kwargs):
        """
        Overrides import_row to skip erroneous rows without stopping the import process.
        """
        import_result = super().import_row(row, instance_loader, **kwargs)

        if import_result.import_type == RowResult.IMPORT_TYPE_ERROR:
            # Mark the row as skipped instead of returning None
            import_result.import_type = RowResult.IMPORT_TYPE_SKIP
            import_result.errors = []

        return import_result

    class Meta:
        skip_unchanged = True
        report_skipped = False
        raise_errors = False
        import_id_fields = ["student", "date_of_creation"]
        model = ExamResult
        fields = (
            "id",
            "date_of_creation",
            "level",
            "student",
            "teacher",
            "units_covered",
            "attendance_percentage",
            "grammar_score",
            "grammar_total",
            "vocabulary_score",
            "vocabulary_total",
            "reading_score",
            "reading_total",
            "writing_score",
            "writing_total",
            "listening_score",
            "listening_total",
            "speaking_score",
            "speaking_total",
            "teacher_assessment_score",
            "teacher_assessment_total",
            "teacher_notes",
            "teacher_recommendation",
        )
