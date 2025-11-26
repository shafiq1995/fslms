# apps/admin_tools/admin.py
from django.contrib import admin
from .models import ActivityLog
from .models import AdminActionLog

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "created_at")
    list_filter = ("user",)
    search_fields = ("user__username", "message")
    date_hierarchy = "created_at"


@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action_type', 'target_object', 'created_at')
    search_fields = ('admin__username', 'target_object', 'action_type')
    list_filter = ('action_type', 'created_at')