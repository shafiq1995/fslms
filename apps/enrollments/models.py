from django.db import models
from django.conf import settings
from apps.courses.models import Course, Lesson
class Enrollment(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course=models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at=models.DateTimeField(auto_now_add=True)
    status=models.CharField(max_length=20, default='enrolled')
    def __str__(self): return f"{self.user} - {self.course}"
class LessonProgress(models.Model):
    enrollment=models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='progress')
    lesson=models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed=models.BooleanField(default=False); completed_at=models.DateTimeField(null=True,blank=True)
