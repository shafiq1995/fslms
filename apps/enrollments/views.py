from django.shortcuts import render, redirect, get_object_or_404
from .models import Enrollment
from apps.courses.models import Course
from django.contrib.auth.decorators import login_required
@login_required
def enroll_confirm(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    Enrollment.objects.get_or_create(user=request.user, course=course)
    return render(request,'pages/enrollment_confirmation.html',{'course':course})
@login_required
def my_enrollments(request):
    qs = Enrollment.objects.filter(user=request.user).select_related('course')
    return render(request,'students/student_dashboard.html',{'enrollments':qs})
