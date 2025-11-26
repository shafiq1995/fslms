from django.db import models
from django.conf import settings


class LearnerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='learnerprofile')

    student_id = models.CharField(max_length=120, blank=True)
    education_level = models.CharField(max_length=120, blank=True)
    institution_name = models.CharField(max_length=255, blank=True)
    learning_goal = models.TextField(blank=True)
    preferred_language = models.CharField(max_length=50, blank=True)
    interests = models.TextField(blank=True, help_text="Comma-separated interests")
    resume = models.FileField(upload_to='learners/resumes/', blank=True, null=True)
    special_needs = models.TextField(blank=True)
    guardian_name = models.CharField(max_length=150, blank=True)
    emergency_contact = models.CharField(max_length=50, blank=True)
    total_courses_enrolled = models.PositiveIntegerField(default=0)
    total_certificates = models.PositiveIntegerField(default=0)
    learning_hours = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} (Learner)"

