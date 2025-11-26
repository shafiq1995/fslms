# apps/admin_tools/utils.py
from .models import AdminActionLog, ActivityLog


def log_admin_action(admin_user, action_type, target_object, details: str = ""):
    """
    Create a structured admin action log entry.
    Used for explicit admin actions (approve course, delete user, etc).
    """
    if admin_user is None:
        return
    AdminActionLog.objects.create(
        admin=admin_user,
        action_type=action_type,
        target_object=str(target_object),
        details=details,
    )


def log_activity(message: str, user=None):
    """
    Lightweight activity log for general events (e.g., course created via signals).
    """
    if user is None:
        # optional: allow anonymous logs by skipping if user is missing
        return
    ActivityLog.objects.create(
        user=user,
        message=message,
    )
