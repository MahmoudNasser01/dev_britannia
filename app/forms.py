from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

from .models import User, Student, CourseLevel

class StudentSignupForm(UserCreationForm):
    full_name = forms.CharField(max_length=255, required=True)
    passport_number = forms.CharField(max_length=50, required=True)
    country = CountryField(blank_label="Select Country").formfield(
        required=True, widget=CountrySelectWidget()
    )
    level = forms.ModelChoiceField(queryset=CourseLevel.objects.all(), required=False)
    phone_number = forms.CharField(max_length=20, required=True)
    gender = forms.ChoiceField(
        choices=(('Male', 'Male'), ('Female', 'Female')),
        required=True
    )
    date_of_birth = forms.DateField(required=False)

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', 'full_name', 'passport_number', 'country', 'gender', 'level')


    def clean_passport_number(self):
        # Check if passport number is unique
        if Student.objects.filter(passport_number=self.cleaned_data['passport_number']).exists():
            raise forms.ValidationError("Passport number already exists")
        return self.cleaned_data['passport_number']


    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True

        if commit:
            user.save()
            Student.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                passport_number=self.cleaned_data['passport_number'],
                country=self.cleaned_data['country'],
                level=self.cleaned_data['level'],
                phone_number=self.cleaned_data['phone_number'],
                gender=self.cleaned_data['gender'],
                date_of_birth=self.cleaned_data['date_of_birth'],
                is_approved=False
            )
        # Add user to student group
        group = Group.objects.get(name='Students')
        user.groups.add(group)
        return user