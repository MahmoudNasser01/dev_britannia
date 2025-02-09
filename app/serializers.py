from django.contrib.auth.models import Group
from rest_framework import serializers
from .models import User, CourseLevel, Student, Teacher, ExamResult
from django.contrib.auth import get_user_model


User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(max_length=255)
    student_id = serializers.CharField(max_length=50)
    passport_number = serializers.CharField(max_length=50, required=False, allow_null=True)
    country = serializers.CharField(max_length=100)
    phone_number = serializers.CharField(max_length=20)
    level = serializers.PrimaryKeyRelatedField(queryset=CourseLevel.objects.all())

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'student_id', 'passport_number', 'country', 'phone_number', 'level']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Extract student data
        student_data = {
            'full_name': validated_data.pop('full_name'),
            'student_id': validated_data.pop('student_id'),
            'passport_number': validated_data.pop('passport_number', None),
            'country': validated_data.pop('country'),
            'level': validated_data.pop('level'),
            'phone_number': validated_data.pop('phone_number')
        }

        # Create the User
        user = User.objects.create(**validated_data)
        user.is_staff = True
        user.save()
        # add user to student group
        group, _ = Group.objects.get_or_create(name='Students')
        user.groups.add(group)
        # Create the Student and connect it to the User
        Student.objects.create(user=user, **student_data)

        return user




class CourseLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseLevel
        fields = ['name', 'order']

class StudentSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    is_active = serializers.BooleanField(source='user.is_active')
    class Meta:
        model = Student
        fields = ['email', 'full_name', 'student_id', 'passport_number', 'country', 'level', 'is_active']

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = '__all__'

class ExamResultSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    teacher = TeacherSerializer(read_only=True)
    level = CourseLevelSerializer(read_only=True)

    class Meta:
        model = ExamResult
        fields = '__all__'


class ProfileExams(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    level = CourseLevelSerializer(read_only=True)

    class Meta:
        model = ExamResult
        fields = '__all__'



class StudentProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    is_active = serializers.BooleanField(source='user.is_active')
    exams = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['email', 'full_name', 'student_id', 'passport_number', 'country', 'level', 'is_active', 'exams']


    def get_exams(self, obj):
        exams = ExamResult.objects.filter(student=obj)
        return ProfileExams(exams, many=True).data
