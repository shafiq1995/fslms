from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch
from django.apps import apps
from django.utils import timezone

from apps.courses.models import Course, Section, Lesson, Enrollment, LessonProgress
from apps.courses.forms import CourseForm, SectionForm, LessonForm
from apps.certificates.models import Certificate

from apps.instructor_tool.models import InstructorActivity
from apps.courses.services import recalc_course_progress

def is_instructor(user):
    return user.is_authenticated and user.role in ["instructor", "admin"]

# ========== DASHBOARD ==========
@login_required
@user_passes_test(is_instructor)
def instructor_dashboard(request):
    stats = {
        "total_courses": Course.objects.filter(instructor=request.user).count(),
        "total_sections": Section.objects.filter(course__instructor=request.user).count(),
        "total_lessons": Lesson.objects.filter(section__course__instructor=request.user).count(),
        "pending_courses": Course.objects.filter(
            instructor=request.user,
            status=Course.STATUS_PENDING,
        ).count(),
    }

    recent_courses = Course.objects.filter(instructor=request.user).order_by("-created_at")[:6]
    recent_activities = InstructorActivity.objects.filter(instructor=request.user).order_by("-timestamp")[:10]

    return render(request, "instructor_tool/dashboard.html", {
        "stats": stats,
        "recent_courses": recent_courses,
        "recent_activities": recent_activities,
    })


# ========== COURSE LIST ==========
@login_required
@user_passes_test(is_instructor)
def course_list(request):
    courses = (
        Course.objects.filter(instructor=request.user)
        .select_related("category")
        .defer("description")
        .order_by("-created_at")
    )
    return render(request, "instructor_tool/course_list.html", {"courses": courses})


# ========== COURSE MANAGEMENT ==========
# apps/instructor_tool/views.py  (or your relevant app)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.courses.models import Course, Section
from apps.instructor_tool.forms import SectionForm  # adjust import path

@login_required
def course_manage(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Ensure only instructor or admin can edit
    if request.user != course.instructor and not request.user.is_staff:
        messages.error(request, "You don't have permission to edit this course.")
        return redirect("instructor_tool:course_list")

    # Create SectionForm and handle POST
    section_form = SectionForm()
    if request.method == "POST":
        section_form = SectionForm(request.POST)
        if section_form.is_valid():
            section = section_form.save(commit=False)
            section.course = course

            # ✅ Automatically set the next order number
            last_section = course.sections.order_by('-order').first()
            section.order = (last_section.order + 1) if last_section else 1

            section.save()
            messages.success(request, f"Section '{section.title}' added successfully!")
            return redirect("instructor_tool:course_manage", course_id=course.id)
        else:
            messages.error(request, "Please correct the form errors.")

    # Get all sections of this course
    sections = (
        Section.objects.filter(course=course)
        .prefetch_related(
            "lessons",
            "lessons__attachments",
        )
    )

    return render(request, "instructor_tool/course_manage.html", {
        "course": course,
        "sections": sections,
        "section_form": section_form,
    })


@login_required
@user_passes_test(is_instructor)
def course_progress(request, course_id):
    """Show student progress and engagement for a course."""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)

    # Ensure stored progress is current
    try:
        recalc_course_progress(course, issued_by=request.user)
    except Exception:
        pass

    # All enrollments for this course (canonical Enrollment has user, not student)
    enrollments = (
        Enrollment.objects.filter(course=course)
        .select_related("user")
        .order_by("-date_enrolled")
    )

    # All lessons in this course (used in template)
    lessons = list(
        Lesson.objects.filter(section__course=course)
        .order_by("section__order", "order", "id")
    )

    progress_data = []
    total_progress = 0
    completed_enrollments = 0
    lesson_completion = {lesson.id: 0 for lesson in lessons}

    for enrollment in enrollments:
        # Map lesson_id -> is_completed for this enrollment
        lp_qs = LessonProgress.objects.filter(enrollment=enrollment)
        lesson_map = {lp.lesson_id: lp.is_completed for lp in lp_qs}

        # Prefer stored progress field; fallback to computed
        progress = float(enrollment.progress or 0)
        if progress == 0 and lessons:
            total = len(lessons)
            completed_count = sum(1 for done in lesson_map.values() if done)
            progress = round((completed_count / total) * 100, 1) if total > 0 else 0.0

        total_progress += progress
        if progress >= 100:
            completed_enrollments += 1

        # count lesson completion per lesson
        for lesson_id, done in lesson_map.items():
            if done and lesson_id in lesson_completion:
                lesson_completion[lesson_id] += 1

        progress_data.append(
            {
                "student": enrollment.user,
                "progress": progress,
                "lessons": lesson_map,
                "enrolled_at": enrollment.date_enrolled,
            }
        )

    avg_progress = round(total_progress / len(enrollments), 1) if enrollments else 0.0
    completion_rate = round((completed_enrollments / len(enrollments)) * 100, 1) if enrollments else 0.0

    next_live = (
        Lesson.objects.filter(section__course=course, lesson_type=Lesson.TYPE_LIVE, scheduled_at__isnull=False)
        .order_by("scheduled_at")
        .first()
    )

    context = {
        "course": course,
        "enrollments": enrollments,
        "lessons": lessons,
        "progress_data": progress_data,
        "avg_progress": avg_progress,
        "completion_rate": completion_rate,
        "lesson_completion": lesson_completion,
        "next_live": next_live,
    }
    return render(request, "instructor_tool/course_progress.html", context)


@login_required
@user_passes_test(is_instructor)
def course_students(request, course_id):
    """List students enrolled in a course for the instructor."""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    enrollments = (
        Enrollment.objects.filter(course=course)
        .select_related("user", "user__profile")
        .order_by("-date_enrolled")
    )
    return render(
        request,
        "instructor_tool/course_students.html",
        {"course": course, "enrollments": enrollments},
    )


@login_required
@user_passes_test(is_instructor)
def course_student_profile(request, course_id, user_id):
    """View a specific student's profile for this course (instructor-only)."""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    enrollment = Enrollment.objects.filter(course=course, user_id=user_id).select_related("user").first()
    if not enrollment:
        messages.error(request, "Student is not enrolled in this course.")
        return redirect("instructor_tool:course_students", course_id=course.id)

    student = enrollment.user
    profile = getattr(student, "profile", None)
    return render(
        request,
        "instructor_tool/student_profile.html",
        {"course": course, "student": student, "profile": profile, "enrollment": enrollment},
    )


@login_required
@user_passes_test(is_instructor)
def students_overview(request):
    """Show all instructor courses with enrolled students (accordion)."""
    courses = (
        Course.objects.filter(instructor=request.user)
        .defer("description")
        .prefetch_related(
            Prefetch(
                "enrollments",
                queryset=Enrollment.objects.select_related("user", "user__profile").order_by("-date_enrolled"),
            )
        )
        .order_by("-created_at")
    )
    return render(request, "instructor_tool/students_overview.html", {"courses": courses})


@login_required
@user_passes_test(is_instructor)
def course_certificates(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    certs = Certificate.objects.filter(course=course).select_related("user").order_by("-issued_at")
    return render(request, "instructor_tool/course_certificates.html", {"course": course, "certificates": certs})


@login_required
@user_passes_test(is_instructor)
def reissue_certificate(request, course_id, cert_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    cert = get_object_or_404(Certificate, id=cert_id, course=course)
    cert.issued_at = timezone.now()
    cert.serial = f"{cert.serial}-R{int(cert.issued_at.timestamp())}"
    cert.save(update_fields=["issued_at", "serial"])
    messages.success(request, "Certificate reissued.")
    return redirect("instructor_tool:course_certificates", course_id=course.id)


@login_required
@user_passes_test(is_instructor)
def resubmit_course(request, course_id):
    """
    Allow an instructor to resubmit a draft/rejected course for approval (sets status to pending).
    """
    course = get_object_or_404(Course, id=course_id, instructor=request.user)

    if request.method != "POST":
        messages.error(request, "Please resubmit from the course page.")
        return redirect("instructor_tool:course_manage", course_id=course.id)

    if course.status not in [Course.STATUS_DRAFT, Course.STATUS_REJECTED]:
        messages.info(request, "Only draft or rejected courses can be resubmitted.")
        return redirect("instructor_tool:course_manage", course_id=course.id)

    if not course.category or not course.short_description:
        messages.error(request, "Please add a category and a short description before resubmitting.")
        return redirect("instructor_tool:course_manage", course_id=course.id)

    course.status = Course.STATUS_PENDING
    course.status_note = "Resubmitted for approval"
    course.save(update_fields=["status", "status_note", "updated_at"])
    messages.success(request, f"Course '{course.title}' resubmitted for approval.")
    return redirect("instructor_tool:course_manage", course_id=course.id)



# ========== SECTION MANAGEMENT ==========
@login_required
@user_passes_test(is_instructor)
def section_manage(request, course_id, section_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    section = get_object_or_404(Section, id=section_id, course=course)

    if request.method == "POST":
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, f"Section '{section.title}' updated successfully.")
            # Log activity
            InstructorActivity.objects.create(
                instructor=request.user,
                course=course,
                action="edited_section"
            )
            return redirect("instructor_tool:course_manage", course_id=course.id)
    else:
        form = SectionForm(instance=section)

    return render(request, "instructor_tool/section_manage.html", {
        "form": form,
        "section": section,
        "course": course,
    })

# ========== LESSON MANAGEMENT ==========
@login_required
@user_passes_test(is_instructor)
def lesson_manage(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    lesson = get_object_or_404(Lesson, id=lesson_id, section__course=course)
    section = lesson.section

    if request.method == "POST":
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, f"Lesson '{lesson.title}' updated successfully.")
            InstructorActivity.objects.create(instructor=request.user, course=course, action="edited_lesson")
            return redirect("instructor_tool:course_manage", course_id=course.id)
    else:
        form = LessonForm(instance=lesson)

    return render(request, "instructor_tool/lesson_manage.html", {
        "form": form,
        "lesson": lesson,
        "section": section,
        "course": course,
    })


# ========== CREATE SECTION ==========
@login_required
@user_passes_test(is_instructor)
def create_section(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    if request.method == "POST":
        form = SectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)
            section.course = course
            section.save()
            messages.success(request, "Section added successfully.")
            return redirect("instructor_tool:course_manage", course_id=course.id)
    else:
        form = SectionForm()
    # When instructor creates a section
    log_activity(request.user, "added_section", course)

    return render(request, "instructor_tool/section_manage.html", {"form": form, "course": course})


# ========== CREATE LESSON ==========
@login_required
@user_passes_test(is_instructor)
def create_lesson(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    if request.method == "POST":
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.section = section
            lesson.save()
            messages.success(request, "Lesson added successfully.")
            return redirect("instructor_tool:section_manage", section_id=section.id)
    else:
        form = LessonForm()
    return render(request, "instructor_tool/lesson_manage.html", {"form": form, "section": section, "course": section.course})


# ========== MARK LESSON COMPLETE ==========
@login_required
@user_passes_test(is_instructor)
def mark_lesson_complete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    # Mark lesson as completed globally and update all enrollments' progress
    from apps.courses.services import mark_lesson_for_all_enrollments

    lesson.is_completed = True
    lesson.save(update_fields=["is_completed"])

    try:
        mark_lesson_for_all_enrollments(lesson, completed=True, marked_by=request.user)
    except Exception:
        pass

    messages.success(request, f"Lesson '{lesson.title}' marked as completed for all enrolled students.")
    return redirect("instructor_tool:course_manage", course_id=lesson.section.course.id)


# ========== INSTRUCTOR PUBLIC LIST ==========
def instructor_list(request):
    User = apps.get_model("accounts", "User")
    q = request.GET.get("q", "")
    instructors = User.objects.filter(role="instructor", is_active=True)
    if q:
        instructors = instructors.filter(username__icontains=q)
    paginator = Paginator(instructors, 12)
    page = request.GET.get("page")
    instructors = paginator.get_page(page)
    return render(request, "instructor_tool/instructor_list.html", {"instructors": instructors, "q": q})


# ========== INSTRUCTOR PUBLIC DETAIL ==========
def instructor_detail(request, instructor_id):
    User = apps.get_model("accounts", "User")
    instructor = get_object_or_404(User, id=instructor_id)
    if instructor.role not in ("instructor", "admin"):
        messages.error(request, "This user is not available as an instructor profile.")
        return redirect("home:home")
    courses = Course.objects.filter(
        instructor=instructor,
        status=Course.STATUS_APPROVED,
    )

    return render(request, "instructor_tool/instructor_detail.html", {"instructor": instructor, "courses": courses})
