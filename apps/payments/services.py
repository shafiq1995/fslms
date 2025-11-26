from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.courses.models import Enrollment
from apps.admin_tools.utils import log_admin_action
from .models import Payment


@transaction.atomic
def approve_payment(payment: Payment, admin_user=None):
    """
    Approve a pending payment, mark status, ensure enrollment exists, and log the action.
    """
    if payment.status != Payment.STATUS_PENDING:
        raise ValueError("Only pending payments can be approved.")

    payment.status = Payment.STATUS_COMPLETED
    payment.approved_by = admin_user
    payment.approved_at = timezone.now()
    payment.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

    Enrollment.objects.get_or_create(
        user=payment.user,
        course=payment.course,
        defaults={"is_active": True},
    )

    log_admin_action(
        admin_user,
        "Approved Payment",
        f"Payment #{payment.id}",
        details=f"User={payment.user.username}, Course={payment.course.title}",
    )


@transaction.atomic
def reject_payment(payment: Payment, admin_user=None, note: str = ""):
    if payment.status != Payment.STATUS_PENDING:
        raise ValueError("Only pending payments can be rejected.")

    payment.status = Payment.STATUS_REJECTED
    payment.approved_by = admin_user
    payment.note = note or payment.note
    payment.save(update_fields=["status", "approved_by", "note", "updated_at"])

    log_admin_action(
        admin_user,
        "Rejected Payment",
        f"Payment #{payment.id}",
        details=f"User={payment.user.username}, Course={payment.course.title}, Note={payment.note or ''}",
    )


@transaction.atomic
def refund_payment(payment: Payment, admin_user=None, note: str = ""):
    if payment.status not in (Payment.STATUS_COMPLETED, Payment.STATUS_REJECTED):
        raise ValueError("Only completed or rejected payments can be refunded.")

    payment.status = Payment.STATUS_REFUNDED
    payment.refunded_at = timezone.now()
    payment.approved_by = admin_user or payment.approved_by
    payment.note = note or payment.note
    payment.save(update_fields=["status", "refunded_at", "approved_by", "note", "updated_at"])

    Enrollment.objects.filter(user=payment.user, course=payment.course).update(is_active=False)

    log_admin_action(
        admin_user,
        "Refunded Payment",
        f"Payment #{payment.id}",
        details=f"User={payment.user.username}, Course={payment.course.title}, Note={payment.note or ''}",
    )
