# apps/admin_tools/models.py
from django.db import models
from django.conf import settings


class AdminProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="adminprofile",
    )
    department = models.CharField(max_length=150, blank=True)
    designation = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Admin: {self.user.username}"


class ActivityLog(models.Model):
    """
    Generic activity log (used by log_activity, e.g. when a course is created / approved).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} - {self.user}: {self.message[:50]}..."


class AdminActionLog(models.Model):
    """
    Structured log for admin actions (user changes, approvals, etc.).
    Shown on the Admin Logs page.
    """
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_actions",
    )
    action_type = models.CharField(max_length=100)
    target_object = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.admin.username} - {self.action_type} ({self.created_at:%Y-%m-%d %H:%M})"
