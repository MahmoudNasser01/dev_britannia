from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

from .models import User, Student, CourseLevel

class StudentSignupForm(UserCreationForm):
    full_name = forms.CharField(max_length=255, required=True)
    student_id = forms.CharField(max_length=50, required=True)
    passport_number = forms.CharField(max_length=50, required=False)
    country = forms.CharField(max_length=100, required=True)
    level = forms.ModelChoiceField(queryset=CourseLevel.objects.all(), required=False)

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', 'full_name', 'student_id', 'passport_number', 'country', 'level')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True  # Ensure the user is not a staff member


        if commit:
            user.save()
            Student.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                student_id=self.cleaned_data['student_id'],
                passport_number=self.cleaned_data['passport_number'],
                country=self.cleaned_data['country'],
                level=self.cleaned_data['level']
            )
        # add user to student group
        group = Group.objects.get(name='student')
        user.groups.add(group)
        return user