from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions

from .models import ExamResult, SystemSettings, User
from .pdf_generate import generate_exam_result_pdf_view
from .serializers import RegisterSerializer, ExamResultSerializer, StudentProfileSerializer
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import StudentSignupForm
from django_countries import countries
from drf_spectacular.utils import extend_schema, OpenApiParameter


def student_signup(request):
    if request.method == 'POST':
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # create
            return redirect('admin:index')
        else:
            # return form errors
            return render(request, 'app/student_signup.html', {'form': form})
    else:
        form = StudentSignupForm()
    return render(request, 'app/student_signup.html', {'form': form})

class RegisterView(GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User and Student registered successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserExamResultListView(generics.ListAPIView):
    serializer_class = ExamResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'student_profile'):
            student = user.student_profile
            return ExamResult.objects.filter(student=student)
        else:
            return ExamResult.objects.none()


class StudentProfileView(generics.RetrieveAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.student_profile



class CountryListView(GenericAPIView):

    @extend_schema(
        summary="Get a list of countries",
        description="Returns a list of countries with their codes. Supports searching by name or country code.",
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search for a country by name or code (e.g., 'egy' for Egypt, 'US' for United States).",
                required=False,
                type=str
            ),
        ],
        responses={200: "List of countries"},
    )
    def get(self, request):
        search_query = request.GET.get("search", "").strip().lower()
        
        country_list = [{"code": code, "name": name} for code, name in list(countries)]

        if search_query:
            country_list = [
                country for country in country_list
                if search_query in country["name"].lower() or search_query in country["code"].lower()
            ]

        return Response(country_list)





def activate_user_profile(request, user_id):
    user = User.objects.get(id=user_id)
    user.student_profile.is_approved = True
    user.student_profile.save()
    return redirect('admin:app_user_changelist')




