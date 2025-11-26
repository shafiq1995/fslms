# apps/student_tool/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

@receiver(post_save, dispatch_uid="enrollment_post_save")
def enrollment_post_save(sender, instance, created, **kwargs):
    """
    Log enrollment creation for the canonical courses.Enrollment model.
    Compatible with legacy student_tool Enrollments but prefers instance.user.
    """
    if sender.__name__ != "Enrollment":
        return

    student = getattr(instance, "user", None) or getattr(instance, "student", None)
    course = getattr(instance, "course", None)
    if not student or not course:
        return

    from apps.admin_tools.utils import log_activity

    if created:
        status = getattr(instance, "status", None)
        name = student.get_full_name() or student.username
        if status:
            msg = f"Enrollment created for '{course.title}' by {name} (status: {status})"
        else:
            msg = f"Enrollment created for '{course.title}' by {name}"
        transaction.on_commit(lambda: log_activity(msg, user=student))
