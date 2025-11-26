from __future__ import annotations

from django.utils import timezone
from django.db import transaction
from django.apps import apps

from .models import Enrollment, Lesson, LessonProgress


def recalc_course_progress(course, issued_by=None):
    """
    Recalculate progress for all enrollments in a course.
    """
    enrollments = Enrollment.objects.filter(course=course, is_active=True)
    completed_lessons = list(Lesson.objects.filter(section__course=course, is_completed=True).values_list("id", flat=True))

    for enrollment in enrollments:
        # ensure LessonProgress exists for globally completed lessons
        if completed_lessons:
            for lid in completed_lessons:
                lp, _ = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson_id=lid)
                if not lp.is_completed:
                    lp.is_completed = True
                    lp.completed_at = timezone.now()
                    lp.save(update_fields=["is_completed", "completed_at"])
        recalc_enrollment_progress(enrollment, issued_by=issued_by)


def recalc_enrollment_progress(enrollment: Enrollment, issued_by=None):
    """
    Recalculate progress for a single enrollment and issue a certificate
    when progress reaches 100%.
    """
    lessons = list(Lesson.objects.filter(section__course=enrollment.course))

    # Ensure there is a LessonProgress row per lesson to avoid stale zero progress
    completed = 0
    for lesson in lessons:
        lp, created = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
        # If the lesson was marked globally completed, sync the progress row
        if lesson.is_completed and not lp.is_completed:
            lp.is_completed = True
            lp.completed_at = timezone.now()
            lp.save(update_fields=["is_completed", "completed_at"])
        if lp.is_completed:
            completed += 1

    total_lessons = len(lessons)

    progress = round((completed / total_lessons) * 100, 2) if total_lessons else 0.0

    was_completed = enrollment.is_completed
    enrollment.progress = progress
    enrollment.is_completed = progress >= 100
    if enrollment.is_completed and not was_completed:
        enrollment.completed_at = timezone.now()
    enrollment.last_accessed = timezone.now()
    enrollment.save(update_fields=["progress", "is_completed", "completed_at", "last_accessed"])

    if enrollment.is_completed:
        _issue_certificate_if_missing(enrollment, issued_by=issued_by, progress=progress)


@transaction.atomic
def mark_lesson_completion(enrollment: Enrollment, lesson: Lesson, completed: bool, marked_by=None):
    """
    Mark a lesson complete/incomplete for a specific enrollment,
    then update progress and certificate issuance.
    """
    lp, _ = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
    lp.is_completed = completed
    lp.completed_at = timezone.now() if completed else None
    lp.save(update_fields=["is_completed", "completed_at"])

    recalc_enrollment_progress(enrollment, issued_by=marked_by)


def mark_lesson_for_all_enrollments(lesson: Lesson, completed: bool, marked_by=None):
    """
    Mark a lesson complete/incomplete for every enrollment of the lesson's course.
    """
    enrollments = Enrollment.objects.filter(course=lesson.section.course, is_active=True)
    for enrollment in enrollments:
        mark_lesson_completion(enrollment, lesson, completed, marked_by=marked_by)


def _issue_certificate_if_missing(enrollment: Enrollment, issued_by=None, progress: float = 100.0):
    """
    Lazily issue a certificate when a course is completed.
    """
    Certificate = apps.get_model("certificates", "Certificate")
    existing = Certificate.objects.filter(user=enrollment.user, course=enrollment.course).first()
    if existing:
        return existing

    serial = f"CERT-{enrollment.course.id}-{enrollment.user.id}-{int(timezone.now().timestamp())}"
    return Certificate.objects.create(
        user=enrollment.user,
        course=enrollment.course,
        serial=serial,
        issued_by=issued_by,
        progress_snapshot=progress,
    )
