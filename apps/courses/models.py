from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
import os

class Category(models.Model):
    """Categories for grouping courses (e.g., Web Development, AI, Cybersecurity)."""
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True, help_text="Optional Bootstrap or FontAwesome icon class")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Course Category"
        verbose_name_plural = "Course Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Course(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PENDING, "Pending Approval"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    LEVEL_BEGINNER = "beginner"
    LEVEL_INTERMEDIATE = "intermediate"
    LEVEL_ADVANCED = "advanced"
    LEVEL_CHOICES = [
        (LEVEL_BEGINNER, "Beginner"),
        (LEVEL_INTERMEDIATE, "Intermediate"),
        (LEVEL_ADVANCED, "Advanced"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)  # full description
    language = models.CharField(max_length=50, default="en")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default=LEVEL_BEGINNER)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses'
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    status_note = models.TextField(blank=True, help_text="Optional notes for approval/rejection.")
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_courses",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    thumbnail = models.ImageField(upload_to="course_thumbnails/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def thumbnail_url(self):
        """Return thumbnail URL or a placeholder if not available"""
        if self.thumbnail:
            return self.thumbnail.url
        return settings.STATIC_URL + "images/default_course.jpg"

    def is_published(self):
        return self.status == self.STATUS_PUBLISHED

    def __str__(self):
        return self.title


class Section(models.Model):
    course = models.ForeignKey('Course', related_name='sections', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('course', 'order')
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"




class Lesson(models.Model):
    TYPE_LIVE = "live"
    TYPE_LECTURE = "lecture"
    TYPE_ASSIGNMENT = "assignment"
    TYPE_QUIZ = "quiz"
    LESSON_TYPE_CHOICES = [
        (TYPE_LIVE, "Live class"),
        (TYPE_LECTURE, "Lecture"),
        (TYPE_ASSIGNMENT, "Assignment"),
        (TYPE_QUIZ, "Quiz"),
    ]

    section = models.ForeignKey('Section', on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)
    video = models.FileField(upload_to='lessons/videos/', blank=True, null=True)
    attachment = models.FileField(upload_to='lessons/files/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPE_CHOICES, default=TYPE_LECTURE)
    is_published = models.BooleanField(default=False)
    join_link = models.URLField(blank=True, null=True, help_text="Link to live session (Zoom, Meet, etc.)")
    scheduled_at = models.DateTimeField(null=True, blank=True, help_text="Scheduled date/time for live classes.")
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    resource_links = models.TextField(blank=True, help_text="Optional external resource links (one per line).")
    is_completed = models.BooleanField(default=False, help_text="Marked completed by instructor/admin")
    is_preview = models.BooleanField(default=False, help_text="Allow non-enrolled users to preview this lesson")

    def __str__(self):
        return f"{self.title} ({self.section.title})"

    class Meta:
        ordering = ['order']




class LessonAttachment(models.Model):
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='lessons/files/')
    title = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title if self.title else os.path.basename(self.file.name)

    class Meta:
        ordering = ['uploaded_at']


class CourseApprovalLog(models.Model):
    ACTION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='approval_logs')
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    reason = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.title} - {self.action} by {self.admin}"


class Enrollment(models.Model):
    """
    Represents a student's enrollment in a specific course.
    Tracks progress, completion, and timestamps.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey("Course", on_delete=models.CASCADE, related_name="enrollments")
    is_active = models.BooleanField(default=True)
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Completion percentage.")
    is_completed = models.BooleanField(default=False)
    date_enrolled = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "course")
        ordering = ["-date_enrolled"]

    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"

    def update_progress(self):
        """
        Auto-calculate progress based on completed lessons.
        """
        total_lessons = Lesson.objects.filter(section__course=self.course).count()
        completed_lessons = LessonProgress.objects.filter(
            enrollment=self,
            is_completed=True
        ).count()

        if total_lessons > 0:
            self.progress = round((completed_lessons / total_lessons) * 100, 2)
        else:
            self.progress = 0

        was_completed = self.is_completed
        self.is_completed = self.progress >= 100
        if self.is_completed and not was_completed:
            self.completed_at = timezone.now()
        self.last_accessed = timezone.now()
        self.save()


class LessonProgress(models.Model):
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="lesson_progress"
    )
    lesson = models.ForeignKey(
        "Lesson",
        on_delete=models.CASCADE,
        related_name="progress_records"
    )
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("enrollment", "lesson")

    def __str__(self):
        return f"{self.enrollment.user.username} - {self.lesson.title} ({'Done' if self.is_completed else 'Pending'})"
