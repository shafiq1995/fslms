from django.db import models
from django.conf import settings
from apps.courses.models import Course


from django.db import models
from django.conf import settings
from apps.courses.models import Course


class InstructorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='instructorprofile')

    # Public-facing / CV
    professional_title = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    education = models.CharField(max_length=255, blank=True)
    experience_years = models.PositiveIntegerField(default=0)

    # Skills / expertise
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    expertise_area = models.CharField(max_length=255, blank=True)
    languages = models.CharField(max_length=255, blank=True, help_text="Comma-separated languages taught")

    # Documents
    cv_resume = models.FileField(upload_to='instructors/cv/', blank=True, null=True)
    id_verification = models.FileField(upload_to='instructors/id_docs/', blank=True, null=True)
    signature_image = models.ImageField(upload_to='instructors/signatures/', blank=True, null=True)

    # Payment / payouts
    bank_account = models.CharField(max_length=255, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)

    # Platform metadata
    approved_by_admin = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Statistics (maintained by signals/tasks)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_courses = models.PositiveIntegerField(default=0)
    total_students = models.PositiveIntegerField(default=0)

    # Social links (duplicate optional)
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    website = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username




class InstructorActivity(models.Model):
    ACTION_CHOICES = [
        ('created_course', 'Created a Course'),
        ('updated_course', 'Updated a Course'),
        ('deleted_course', 'Deleted a Course'),
        ('added_section', 'Added a Section'),
        ('edited_section', 'Edited a Section'),
        ('deleted_section', 'Deleted a Section'),
        ('added_lesson', 'Added a Lesson'),
        ('edited_lesson', 'Edited a Lesson'),
        ('deleted_lesson', 'Deleted a Lesson'),
    ]

    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Instructor Activity"
        verbose_name_plural = "Instructor Activities"

    def __str__(self):
        return f"{self.instructor.username} - {self.get_action_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
