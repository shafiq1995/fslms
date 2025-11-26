from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    """
    Custom user with a simple role system.
    """
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"
    # Backwards compatibility for old rows that used "learner"
    LEARNER = "learner"

    ROLE_CHOICES = (
        (STUDENT, "Student"),
        (INSTRUCTOR, "Instructor"),
        (ADMIN, "Admin"),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=STUDENT,
    )
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    # For instructors/admins that need manual approval
    is_approved = models.BooleanField(default=False)

    # Helper methods used throughout the project
    def is_student(self):
        return self.role in (self.STUDENT, self.LEARNER)

    def is_instructor(self):
        return self.role == self.INSTRUCTOR

    def is_admin_role(self):
        return self.role == self.ADMIN

    @property
    def effective_role(self):
        """
        Safe role accessor for templates.
        """
        return self.role or self.STUDENT

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    """
    Common profile info for all users (student, instructor, admin).
    """

    # String constants kept for backwards-compatibility in code
    ROLE_ADMIN = "admin"
    ROLE_INSTRUCTOR = "instructor"
    ROLE_LEARNER = "learner"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    # Basic / common fields
    phone = models.CharField(max_length=30, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(
        upload_to="profiles/", blank=True, null=True
    )

    # Social links
    linkedin_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    website = models.URLField(blank=True)

    # Account metadata
    is_verified = models.BooleanField(default=False)
    preferred_language = models.CharField(max_length=50, blank=True)
    timezone = models.CharField(max_length=50, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Convenience
    def full_name(self):
        full = f"{self.user.first_name} {self.user.last_name}".strip()
        return full or self.user.username

    def __str__(self):
        return f"{self.user.username} ({self.user.role})"
