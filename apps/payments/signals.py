# apps/payments/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction

@receiver(pre_save, dispatch_uid="payment_pre_save")
def payment_pre_save(sender, instance, **kwargs):
    # attach previous status for comparison
    if sender.__name__ != "Payment":
        return
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._previous_status = getattr(old, "status", None)
        except sender.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None

@receiver(post_save, dispatch_uid="payment_post_save")
def payment_post_save(sender, instance, created, **kwargs):
    if sender.__name__ != "Payment":
        return
    from apps.admin_tools.utils import log_activity
    user = getattr(instance, "user", None)
    course = getattr(instance, "course", None)
    new_status = getattr(instance, "status", None)
    prev = getattr(instance, "_previous_status", None)

    # created -> log submission
    if created:
        msg = f"Payment submitted by {user.username if user else 'Unknown'} for '{course.title if course else 'N/A'}' - Tx: {getattr(instance, 'provider_tx_id', '')} (status: {new_status})"
        transaction.on_commit(lambda: log_activity(msg, user=user))
        return

    # status changed -> log
    if prev != new_status:
        if new_status == "Approved":
            msg = f"Payment APPROVED for '{course.title if course else 'N/A'}' by {user.username if user else 'System'} (Tx: {getattr(instance, 'provider_tx_id', '')})"
        elif new_status == "Rejected":
            msg = f"Payment REJECTED for '{course.title if course else 'N/A'}' by {user.username if user else 'System'} (Tx: {getattr(instance, 'provider_tx_id', '')})"
        elif new_status == "Refunded":
            msg = f"Payment REFUNDED for '{course.title if course else 'N/A'}' (Tx: {getattr(instance, 'provider_tx_id', '')})"
        else:
            msg = f"Payment status changed to {new_status} for '{course.title if course else 'N/A'}' (Tx: {getattr(instance, 'provider_tx_id', '')})"
        transaction.on_commit(lambda: log_activity(msg, user=getattr(instance, "approved_by", user)))
