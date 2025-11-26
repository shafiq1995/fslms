# apps/accounts/management/commands/check_db_columns.py
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connection
from django.db.utils import OperationalError

class Command(BaseCommand):
    help = "Checks for missing database columns in all installed apps and suggests migration fixes."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("🔍 Checking database schema consistency...\n"))

        missing_columns = {}
        with connection.cursor() as cursor:
            for model in apps.get_models():
                table = model._meta.db_table
                try:
                    cursor.execute(f"PRAGMA table_info({table});")
                    db_columns = {col[1] for col in cursor.fetchall()}
                except OperationalError as e:
                    self.stdout.write(self.style.ERROR(f"❌ Could not inspect table '{table}': {e}"))
                    continue

                model_fields = {
                    f.column
                    for f in model._meta.get_fields()
                    if hasattr(f, "column") and f.column
                }

                # Detect missing columns
                missing = model_fields - db_columns
                if missing:
                    missing_columns[table] = sorted(list(missing))

        if not missing_columns:
            self.stdout.write(self.style.SUCCESS("✅ All database tables are in sync with models!"))
        else:
            self.stdout.write(self.style.WARNING("\n⚠️ Missing columns detected:\n"))
            for table, columns in missing_columns.items():
                self.stdout.write(self.style.WARNING(f"  • {table}: {', '.join(columns)}"))
            self.stdout.write("\n💡 Suggested fix:")
            self.stdout.write(self.style.HTTP_INFO(
                "  python manage.py makemigrations\n  python manage.py migrate"
            ))

        self.stdout.write(self.style.MIGRATE_HEADING("\nCheck completed.\n"))
