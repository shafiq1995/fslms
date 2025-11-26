from django.contrib import admin
from .models import InstructorProfile, InstructorActivity


from django.contrib import admin
from .models import InstructorProfile

@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'professional_title', 'approved_by_admin', 'rating', 'total_courses', 'is_active')
    list_filter = ('approved_by_admin', 'is_active')
    search_fields = ('user__username', 'user__email', 'professional_title', 'skills')


@admin.register(InstructorActivity)
class InstructorActivityAdmin(admin.ModelAdmin):
    list_display = ('instructor', 'action', 'course', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('instructor__username', 'course__title')
    ordering = ('-timestamp',)
