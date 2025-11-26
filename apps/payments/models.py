from django.db import models
from django.conf import settings
from apps.courses.models import Course


class Payment(models.Model):
    PROVIDER_BKASH = "bkash"
    PROVIDER_NAGAD = "nagad"
    PROVIDER_ROCKET = "rocket"
    PROVIDER_BANK = "bank"
    PROVIDER_OTHER = "other"

    PAYMENT_PROVIDERS = [
        (PROVIDER_BKASH, "bKash"),
        (PROVIDER_NAGAD, "Nagad"),
        (PROVIDER_ROCKET, "Rocket"),
        (PROVIDER_BANK, "Bank Transfer"),
        (PROVIDER_OTHER, "Other"),
    ]

    STATUS_PENDING = "Pending"
    STATUS_COMPLETED = "Completed"
    STATUS_FAILED = "Failed"
    STATUS_REJECTED = "Rejected"
    STATUS_REFUNDED = "Refunded"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="payments", on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course, related_name="payments", on_delete=models.CASCADE
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    provider = models.CharField(max_length=50, choices=PAYMENT_PROVIDERS)
    provider_tx_id = models.CharField("Transaction ID", max_length=255)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="approved_payments",
        on_delete=models.SET_NULL,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["provider"]),
            models.Index(fields=["provider_tx_id"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.provider})"
