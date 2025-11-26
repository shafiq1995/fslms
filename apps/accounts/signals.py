from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps

from .models import UserProfile


def _ensure_role_profiles(user):
    """
    Ensure the correct role-specific profile exists for this user.
    Uses apps.get_model to avoid circular imports.
    """
    try:
        InstructorProfile = apps.get_model("instructor_tool", "InstructorProfile")
        LearnerProfile = apps.get_model("student_tool", "LearnerProfile")
        AdminProfile = apps.get_model("admin_tools", "AdminProfile")
    except LookupError:
        # App not loaded yet; fail silently
        return

    role = getattr(user, "role", None)
    if not role:
        return

    if getattr(user, "is_instructor", None) and user.is_instructor():
        InstructorProfile.objects.get_or_create(user=user)
    elif getattr(user, "is_student", None) and user.is_student():
        LearnerProfile.objects.get_or_create(user=user)
    elif getattr(user, "is_admin_role", None) and user.is_admin_role():
        AdminProfile.objects.get_or_create(user=user)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Always ensure a UserProfile exists for every user,
    and create role-specific profiles when appropriate.
    """
    UserProfile.objects.get_or_create(user=instance)
    # Whether created or role changed later, ensure role profiles exist
    _ensure_role_profiles(instance)


@receiver(post_save, sender=UserProfile)
def ensure_role_profiles_from_profile(sender, instance, created, **kwargs):
    """
    When a profile is created/updated, re-check role-specific profiles.
    """
    _ensure_role_profiles(instance.user)
