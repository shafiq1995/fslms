from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course", "amount", "status", "provider", "provider_tx_id", "created_at")
    list_filter = ("status", "provider", "created_at")
    search_fields = ("user__username", "user__email", "provider_tx_id", "course__title")
    readonly_fields = ("created_at", "updated_at")
