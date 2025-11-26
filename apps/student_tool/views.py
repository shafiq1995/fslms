from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from apps.courses.models import Course, Lesson, Section, Enrollment, LessonProgress
from apps.courses.services import mark_lesson_completion, recalc_enrollment_progress
from apps.payments.models import Payment
from apps.certificates.models import Certificate



@login_required
def dashboard(request):
    """Student Dashboard — show enrolled courses, available courses, and pending payments."""
    # Redirect non-student roles to their dashboards
    role = (getattr(request.user, 'role', '') or '').lower()
    if request.user.is_staff or request.user.is_superuser or role == 'admin':
        return redirect('admin_tools:dashboard')
    if role == 'instructor':
        return redirect('instructor_tool:dashboard')
    student = request.user

    # Fetch enrolled courses with related data
    enrolled_courses = (
        Enrollment.objects
        .filter(user=student)
        .select_related("course", "course__category", "course__instructor")
        .order_by("-date_enrolled")
    )

    pending_payments = (
        Payment.objects
        .filter(user=request.user, status=Payment.STATUS_PENDING)
        .select_related("course")
    )

    # Calculate progress for each enrollment (prefetch default)
    lesson_counts = {
        course_id: Lesson.objects.filter(section__course_id=course_id).count()
        for course_id in enrolled_courses.values_list("course_id", flat=True)
    }
    for enrollment in enrolled_courses:
        total_lessons = lesson_counts.get(enrollment.course_id, 0)
        completed_lessons = LessonProgress.objects.filter(
            enrollment=enrollment, is_completed=True
        ).count()
        enrollment.progress = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        try:
            # persist accurate progress for consistency across dashboards
            recalc_enrollment_progress(enrollment, issued_by=request.user)
        except Exception:
            pass

    # Get IDs of enrolled courses
    enrolled_ids = enrolled_courses.values_list("course_id", flat=True)

    # Available courses: exclude enrolled and only show approved/published ones
    available_courses = (
        Course.objects.exclude(id__in=enrolled_ids)
        .filter(status__in=[Course.STATUS_APPROVED, Course.STATUS_PUBLISHED])
        .select_related("instructor", "category")
        .defer("description")
    )

    context = {
        "enrolled_courses": enrolled_courses,
        "available_courses": available_courses,
        "pending_payments": pending_payments,
        "certificates": Certificate.objects.filter(user=student).select_related("course").order_by("-issued_at"),
    }
    return render(request, "student_tool/dashboard.html", context)


@login_required
def certificates_list(request):
    certs = Certificate.objects.filter(user=request.user).select_related("course").order_by("-issued_at")
    return render(request, "student_tool/certificates_list.html", {"certificates": certs})


@login_required
def certificate_detail(request, pk):
    cert = get_object_or_404(
        Certificate.objects.select_related("course", "user"),
        pk=pk,
        user=request.user,
    )
    return render(request, "student_tool/certificate_detail.html", {"certificate": cert})


@login_required
def certificate_download(request, pk):
    """
    Placeholder download view: renders the certificate detail; replace with PDF streaming when ready.
    """
    cert = get_object_or_404(
        Certificate.objects.select_related("course", "user"),
        pk=pk,
        user=request.user,
    )
    # Delegate to shared PDF endpoint
    return redirect("certificates:pdf", pk=cert.pk)


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from apps.courses.models import Course, Enrollment
from apps.payments.forms import StudentPaymentForm  # adjust import if needed


@login_required
def enroll_course(request, course_id):
    """
    Student starts enrollment by submitting a manual payment (bKash, Nagad, Rocket).
    - Creates a Payment with status = Pending
    - Enrollment is created only after admin approval.
    """
    course = get_object_or_404(Course, id=course_id)

    # Block enrollment for unpublished/unapproved courses
    if course.status not in [Course.STATUS_APPROVED, Course.STATUS_PUBLISHED]:
        messages.error(request, "This course is not open for enrollment.")
        return redirect("courses:course_detail", course_id=course.id)

    # If already enrolled (via previously approved payment), don't let them pay again.
    already_enrolled = Enrollment.objects.filter(
        user=request.user,
        course=course,
    ).exists()
    if already_enrolled:
        messages.info(request, "You are already enrolled in this course.")
        return redirect("student_tool:course_detail", course_id=course.id)

    # Prevent duplicate pending/completed payments
    existing_payment = Payment.objects.filter(
        user=request.user,
        course=course,
        status__in=[Payment.STATUS_PENDING, Payment.STATUS_COMPLETED],
    ).first()
    if existing_payment:
        messages.warning(request, "You already have a payment on file for this course.")
        return redirect("student_tool:dashboard")

    if request.method == "POST":
        form = StudentPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            payment.course = course
            payment.amount = course.price  # ensure course price is the source of truth
            # status stays the default = Pending
            payment.save()
            messages.success(
                request,
                "Your payment has been submitted and is pending admin verification.",
            )
            return redirect("student_tool:dashboard")
    else:
        form = StudentPaymentForm()

    context = {
        "course": course,
        "form": form,
    }
    # Use your existing template; adjust path if different
    return render(request, "student_tool/payment_form.html", context)



@login_required
def course_detail(request, course_id):
    """
    Show a detailed view of the student's enrolled course.
    - If enrolled: show lessons, sections, and progress.
    - If not enrolled: show info only.
    """
    course = get_object_or_404(Course, id=course_id)
    user = request.user

    # Check if enrolled (using canonical Enrollment.user)
    enrollment = Enrollment.objects.filter(user=user, course=course).first()

    if not enrollment:
        messages.info(request, "You must enroll in this course to view its contents.")
        return render(
            request,
            "student_tool/course_detail.html",
            {
                "course": course,
                "sections": [],
                "lesson_progress": {},
                "progress": 0,
                "is_enrolled": False,
            },
        )

    # Fetch sections and lessons
    sections = Section.objects.filter(course=course).prefetch_related("lessons")

    # Fetch progress for each lesson
    lesson_progress_qs = LessonProgress.objects.filter(enrollment=enrollment)
    lesson_progress = {lp.lesson_id: lp.is_completed for lp in lesson_progress_qs}

    total_lessons = Lesson.objects.filter(section__course=course).count()
    completed = sum(1 for lp in lesson_progress.values() if lp)
    progress = (completed / total_lessons * 100) if total_lessons > 0 else 0

    context = {
        "course": course,
        "sections": sections,
        "lesson_progress": lesson_progress,
        "progress": progress,
        "is_enrolled": True,
    }
    return render(request, "student_tool/course_detail.html", context)


@login_required
def mark_lesson_complete(request, lesson_id):
    """Mark a lesson as completed for the current student."""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    enrollment = get_object_or_404(
        Enrollment,
        user=request.user,
        course=lesson.section.course,
    )

    lp, _ = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)

    if not lp.is_completed:
        mark_lesson_completion(enrollment, lesson, completed=True, marked_by=request.user)
        messages.success(request, f"Lesson '{lesson.title}' marked as completed.")
    else:
        messages.info(request, f"You already completed '{lesson.title}'.")

    return redirect("student_tool:course_detail", course_id=lesson.section.course.id)
