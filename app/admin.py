from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import models
from django.forms import DateInput
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin

from .models import User, Student, Teacher, ExamResult, CourseLevel, ManagingDirector, SystemSettings
from .recources import ExamResultResource


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['student_id_counter_start']


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'user_type', 'is_active', 'create_student_profile_button')

    def name(self, obj):
        return obj.get_full_name

    def user_type(self, obj):
        if obj.is_student and obj.student_profile.is_approved:
            url = reverse('admin:app_student_change', args=[obj.student_profile.id])
            return mark_safe('<a href="{}">{}</a>'.format(url, "Student"))
        elif obj.is_teacher:
            url = reverse('admin:app_teacher_change', args=[obj.teacher_profile.id])
            return mark_safe('<a href="{}">{}</a>'.format(url, "Teacher"))
        elif obj.is_direct_manager:
            return "Direct Manager"  # Add a link if you have a manager admin page
        elif obj.is_superuser:
            url = reverse('admin:app_user_change', args=[obj.id])
            return mark_safe('<a href="{}">{}</a>'.format(url, "Admin"))
        else:
            return "Not Registered"

    user_type.short_description = "User Type"

    def create_student_profile_button(self, obj):
        """Displays a button to create a student profile if the user is not registered."""
        if not hasattr(obj, 'student_profile'):
            url = reverse('admin:app_student_add') + f"?user={obj.id}&from_users=1"
            return format_html('<a class="button" href="{}">Create Student Profile</a>', url)
        if hasattr(obj, 'student_profile') and not obj.student_profile.is_approved:
            url = reverse('student-profile-activate', args=[obj.id])
            return format_html('<a class="button" href="{}">Activate Student Profile</a>', url)
        return "-"

    create_student_profile_button.short_description = "Actions"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Superusers can see all users
        return qs.filter(id=request.user.id)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ()
        return ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions', 'last_login', 'password')


#     model = User
#     list_display = ('email', 'is_staff', 'is_active')
#     list_filter = ('is_staff', 'is_active')
#     fieldsets = (
#         (None, {'fields': ('email', 'password')}),
#         ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
#     )
#     add_fieldsets = (
#         (
#             None,
#             {
#                 "classes": ("wide",),
#                 "fields": ("username", "usable_password", "password1", "password2"),
#             },
#         ),
#     )
#     search_fields = ('email',)
#     ordering = ('email',)
#
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         if request.user.is_superuser:
#             return qs  # Superusers can see all users
#         if hasattr(request.user, 'student_profile'):
#             return qs.filter(id=request.user.id)  # Students can only see their own profile
#         return qs.none()  # Non-students see no profiles
#
#     def has_change_permission(self, request, obj=None):
#         # Allow students to edit their own profile
#         if obj is not None and hasattr(request.user, 'student_profile') or request.user.is_teacher:
#             return obj.id == request.user.id
#         # Superusers can edit all profiles
#         return super().has_change_permission(request, obj)
#
#     def get_fieldsets(self, request, obj=None):
#         if obj and hasattr(request.user, 'student_profile') and obj.id == request.user.id or request.user.is_teacher or request.user.is_superuser:
#             # Students can only edit email and password
#             return (
#                 (None, {'fields': ('email', 'password', 'is_staff', 'is_active')}),
#             )
#         return super().get_fieldsets(request, obj)

class ExamResultAdminForm(forms.ModelForm):
    class Meta:
        model = ExamResult
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()

        # Validate that the scores do not exceed the total scores
        if cleaned_data.get('grammar') > cleaned_data.get('grammar_total'):
            raise ValidationError(
                f"Grammar score cannot exceed the maximum allowed ({cleaned_data.get('grammar_total')}).")

        if cleaned_data.get('vocabulary') > cleaned_data.get('vocabulary_total'):
            raise ValidationError(
                f"Vocabulary score cannot exceed the maximum allowed ({cleaned_data.get('vocabulary_total')}).")

        if cleaned_data.get('reading') > cleaned_data.get('reading_total'):
            raise ValidationError(
                f"Reading score cannot exceed the maximum allowed ({cleaned_data.get('reading_total')}).")

        if cleaned_data.get('writing') > cleaned_data.get('writing_total'):
            raise ValidationError(
                f"Writing score cannot exceed the maximum allowed ({cleaned_data.get('writing_total')}).")

        if cleaned_data.get('listening') > cleaned_data.get('listening_total'):
            raise ValidationError(
                f"Listening score cannot exceed the maximum allowed ({cleaned_data.get('listening_total')}).")

        if cleaned_data.get('speaking') > cleaned_data.get('speaking_total'):
            raise ValidationError(
                f"Speaking score cannot exceed the maximum allowed ({cleaned_data.get('speaking_total')}).")

        if cleaned_data.get('teacher_assessment') > cleaned_data.get('teacher_assessment_total'):
            raise ValidationError(
                f"Teacher assessment score cannot exceed the maximum allowed ({cleaned_data.get('teacher_assessment_total')}).")

        return cleaned_data


@admin.register(ExamResult)
class ExamResultAdmin(ImportExportModelAdmin):
    form = ExamResultAdminForm
    resource_classes = [ExamResultResource]
    list_display = ('student', 'date_of_creation', 'level', 'total_score', 'total_percentage')
    search_fields = ('student__full_name', 'student__student_id')
    readonly_fields = ('pdf', 'total_score', 'total_percentage')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_teacher:
            return qs
        if hasattr(request.user, 'student_profile'):
            return qs.filter(student=request.user.student_profile)
        return qs.none()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        student_id = request.GET.get('student_id')
        if student_id:
            student = Student.objects.get(id=student_id)
            form.base_fields['student'].initial = student  # Pre-fill the student field
            form.base_fields['level'].initial = student.level  # Pre-fill the level field
        return form

    formfield_overrides = {
        models.DateField: {'widget': DateInput(attrs={'type': 'date'})},
    }

    fieldsets = (
        (None, {
            'fields': ('student', 'teacher', 'level', 'date_of_creation', 'units_covered',
                       ('grammar', 'grammar_total'),
                       ('vocabulary', 'vocabulary_total'),
                       ('reading', 'reading_total'),
                       ('writing', 'writing_total'),
                       ('listening', 'listening_total'),
                       ('speaking', 'speaking_total'),
                       ('teacher_assessment', 'teacher_assessment_total'),
                       'attendance_percentage',
                       'teacher_recommendation',
                       'note',
                       'total_score',
                       'total_percentage',
                       'pdf'
                       )}),

    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'student_id', 'passport_number', 'country', 'level', 'exam_result_actions')
    search_fields = ('full_name', 'student_id', 'passport_number')
    list_filter = ('level',)
    change_form_template = 'admin/student_change_form.html'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == 'user':
                if hasattr(request.user, 'student_profile'):
                    # Filter the user field to show only the current student's user
                    kwargs['queryset'] = User.objects.filter(id=request.user.id)
                else:
                    # If not a student, make the user field empty or return no queryset
                    kwargs['queryset'] = User.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_teacher:
            return qs  # Superusers can see all students
        if hasattr(request.user, 'student_profile'):
            return qs.filter(id=request.user.student_profile.id)  # Students can only see their own profile
        return qs.none()  # Non-students see no profiles

    def has_change_permission(self, request, obj=None):
        # allow teachers to edit student profile
        if obj is not None and request.user.is_superuser:
            return True
        # Allow students to edit their own profile
        if obj is not None and hasattr(request.user, 'student_profile'):
            return obj.id == request.user.student_profile.id

        # Superusers can edit all profiles
        return super().has_change_permission(request, obj)

    def exam_result_actions(self, obj):
        # Link to the admin add view for ExamResult with student_id pre-filled
        return format_html(
            '<a class="button" href="{}"><i class="fa fa-plus-circle"></i>Add Exam Result</a>',
            reverse('admin:app_examresult_add') + f'?student_id={obj.id}'
        )

    exam_result_actions.short_description = 'Exam Result Actions'
    exam_result_actions.allow_tags = True

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        student = self.get_object(request, object_id)
        if student:
            exam_results = ExamResult.objects.filter(student=student)
            extra_context['exam_results'] = exam_results
            # exam could be edit for super user or teacher
            extra_context['can_edit_exam'] = request.user.is_superuser or request.user.is_teacher
        else:
            extra_context['exam_results'] = ExamResult.objects.none()  # Empty queryset if no student
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_changeform_initial_data(self, request):
        """Pre-fill the user field if ?user=<id> is in the URL."""
        user_id = request.GET.get('user')
        if user_id:
            return {'user': user_id}
        return super().get_changeform_initial_data(request)

    def response_add(self, request, obj, post_url_continue=None):
        """Redirect to Users list only if 'from_users' parameter exists."""
        if request.GET.get('from_users') == '1':
            user_list_url = reverse('admin:app_user_changelist')  # Change 'app' to your actual app name
            return redirect(user_list_url)
        return super().response_add(request, obj, post_url_continue)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('full_name',)
    search_fields = ('full_name',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == 'user':
                if hasattr(request.user, 'teacher_profile'):
                    # Filter the user field to show only the current student's user
                    kwargs['queryset'] = User.objects.filter(id=request.user.id)
                else:
                    # If not a student, make the user field empty or return no queryset
                    kwargs['queryset'] = User.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        # allow teachers to edit student profile
        if obj is not None and request.user.is_superuser:
            return True
        # Allow students to edit their own profile
        if obj is not None and request.user.is_teacher:
            return obj.id == request.user.teacher_profile.id

        # Superusers can edit all profiles
        return super().has_change_permission(request, obj)


@admin.register(ManagingDirector)
class ManagingDirectorAdmin(admin.ModelAdmin):
    list_display = ('full_name',)
    search_fields = ('full_name',)


@admin.register(CourseLevel)
class CourseLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    search_fields = ('name',)
