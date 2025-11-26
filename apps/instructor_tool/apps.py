from django.apps import AppConfig

class InstructorToolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.instructor_tool'  # ✅ Must include 'apps.'
