from django.contrib import admin
from django.forms import DateInput
from django.urls import reverse
from django.utils.html import format_html
from .models import User, Student, Teacher, ExamResult, CourseLevel, ManagingDirector
from django.contrib.auth.admin import UserAdmin




admin.site.register(User)
# @admin.register(User)
# class CustomUserAdmin(UserAdmin):
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

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'date_of_creation', 'level', 'total_score', 'total_percentage')
    search_fields = ('student__full_name', 'student__student_id')
    list_filter = ('level__year', 'level__month')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'student_profile'):
            return qs.filter(student=request.user.student_profile)
        return qs.none()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        student_id = request.GET.get('student_id')  # Get student_id from the URL
        if student_id:
            student = Student.objects.get(id=student_id)
            form.base_fields['student'].initial = student  # Pre-fill the student field
            form.base_fields['level'].initial = student.level  # Pre-fill the level field
        return form



@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'student_id', 'country', 'level', 'exam_result_actions')
    search_fields = ('full_name', 'student_id', 'passport_number')
    list_filter = ('level','level__year', 'level__month')
    change_form_template = 'admin/student_change_form.html'


    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_teacher:
            return qs  # Superusers can see all students
        if hasattr(request.user, 'student_profile'):
            return qs.filter(id=request.user.student_profile.id)  # Students can only see their own profile
        return qs.none()  # Non-students see no profiles

    def has_change_permission(self, request, obj=None):
        # Allow students to edit their own profile
        if obj is not None and hasattr(request.user, 'student_profile'):
            return obj.id == request.user.student_profile.id

        # allow teachers to edit student profile
        if obj is not None and request.user.is_teacher:
            return True
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

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('full_name',)
    search_fields = ('full_name',)

@admin.register(ManagingDirector)
class ManagingDirectorAdmin(admin.ModelAdmin):
    list_display = ('full_name',)
    search_fields = ('full_name',)

@admin.register(CourseLevel)
class CourseLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    search_fields = ('name',)





