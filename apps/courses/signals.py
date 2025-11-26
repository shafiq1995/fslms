# apps/courses/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import Course, Enrollment
from apps.admin_tools.utils import log_activity
from .services import _issue_certificate_if_missing


def _instructor_display_name(course: Course) -> str:
    """Helper to safely get instructor display name."""
    instructor = getattr(course, "instructor", None)
    if not instructor:
        return "Unknown instructor"
    full_name = instructor.get_full_name()
    return full_name or instructor.username or "Unknown instructor"


@receiver(post_save, sender=Course, dispatch_uid="courses_course_post_save")
def course_post_save(sender, instance: Course, created, **kwargs):
    """
    Log basic activity when:
    - a course is created
    - a course is saved in an APPROVED/PUBLISHED state
    """
    instructor = getattr(instance, "instructor", None)
    instructor_name = _instructor_display_name(instance)

    # Always run logging after transaction commit
    def _log(message: str):
        transaction.on_commit(
            lambda: log_activity(message, user=instructor)
        )

    if created:
        msg = f"New course created: '{instance.title}' by {instructor_name}"
        _log(msg)
    else:
        # Log when the course is in an "available" state
        status = getattr(instance, "status", None)
        if status in (Course.STATUS_APPROVED, Course.STATUS_PUBLISHED):
            msg = f"Course published/approved: '{instance.title}' by {instructor_name}"
            _log(msg)


@receiver(post_save, sender=Enrollment, dispatch_uid="courses_enrollment_issue_certificate")
def enrollment_issue_certificate(sender, instance: Enrollment, **kwargs):
    """
    Ensure a certificate is issued when an enrollment reaches completion.
    Avoids recursion by only calling the certificate helper (no enrollment save).
    """
    if instance.is_completed or float(instance.progress or 0) >= 100:
        transaction.on_commit(
            lambda: _issue_certificate_if_missing(instance, issued_by=None, progress=float(instance.progress or 100))
        )
