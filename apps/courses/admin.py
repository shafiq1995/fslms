from django.contrib import admin
from .models import CourseApprovalLog
from .models import Category, Course, Section, Lesson
from django.contrib import admin
from .models import Lesson

from django.contrib import admin
from .models import Lesson, LessonAttachment
from django.contrib import admin
from .models import Category


@admin.register(Category)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

class LessonAttachmentInline(admin.TabularInline):
    model = LessonAttachment
    extra = 1


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "title", "section", "is_published", "is_preview", "is_completed", "order"
    )
    list_editable = ("is_published", "is_preview", "is_completed")
    list_filter = ("is_published", "is_preview", "is_completed", "section")
    search_fields = ("title",)
    inlines = [LessonAttachmentInline]



@admin.register(CourseApprovalLog)
class CourseApprovalLogAdmin(admin.ModelAdmin):
    list_display = ('course', 'admin', 'action', 'reason', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('course__title', 'admin__username', 'reason')

