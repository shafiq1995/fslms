from django.db import models
from django.conf import settings
from apps.courses.models import Course


class Certificate(models.Model):
    STATUS_VALID = "valid"
    STATUS_REVOKED = "revoked"
    STATUS_CHOICES = [
        (STATUS_VALID, "Valid"),
        (STATUS_REVOKED, "Revoked"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="certificates")
    serial = models.CharField(max_length=120, unique=True)
    template_name = models.CharField(max_length=120, blank=True, help_text="Identifier of the certificate template.")
    issued_at = models.DateTimeField(auto_now_add=True)
    progress_snapshot = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_VALID)
    download_url = models.CharField(max_length=255, blank=True, help_text="Cached PDF path or URL for download.")
    meta = models.JSONField(blank=True, null=True, help_text="Additional data (dict) for customization.")
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="issued_certificates",
    )

    class Meta:
        unique_together = ("user", "course")
        ordering = ["-issued_at"]
        indexes = [
            models.Index(fields=["serial"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.course} - {self.serial}"
