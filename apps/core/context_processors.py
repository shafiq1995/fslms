# apps/core/context_processors.py
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def user_role_context(request):
    """
    Injects user-role related flags into all templates.
    Safe to use even when the user is anonymous.
    """
    user = getattr(request, "user", None)

    if not getattr(user, "is_authenticated", False):
        return {
            "user_role": None,
            "is_student_user": False,
            "is_instructor_user": False,
            "is_admin_user": False,
        }

    role = getattr(user, "role", None)

    # Backward compatibility: treat 'learner' as student
    is_student = role in ("student", "learner")
    is_instructor = role == "instructor"
    is_admin = role == "admin" or getattr(user, "is_staff", False)

    return {
        "user_role": role,
        "is_student_user": is_student,
        "is_instructor_user": is_instructor,
        "is_admin_user": is_admin,
    }
