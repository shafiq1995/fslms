from django.apps import AppConfig


class StudentToolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.student_tool'

    def ready(self):
        # Import signals here if you have any, NOT models
        try:
            import apps.student_tool.signals
        except ImportError:
            pass
