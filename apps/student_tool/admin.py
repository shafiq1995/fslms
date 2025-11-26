from django.contrib import admin

from .models import LearnerProfile


@admin.register(LearnerProfile)
class LearnerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "education_level", "institution_name", "total_courses_enrolled", "total_certificates")
    list_filter = ("education_level",)
    search_fields = ("user__username", "user__email", "institution_name")
