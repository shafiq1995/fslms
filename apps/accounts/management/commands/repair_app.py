import sys
import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = (
        "Safely repairs migrations for a specific Django app.\n"
        "It regenerates missing migrations, resets migration history, "
        "and reapplies them in safe (fake-initial) mode without losing data."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "app_label",
            type=str,
            help="App label to repair (e.g. 'student_tool', 'instructor_tool', or 'accounts')."
        )

    def handle(self, *args, **options):
        app_label = options["app_label"]

        # Step 1 — Validate the app
        try:
            app_config = apps.get_app_config(app_label)
        except LookupError:
            raise CommandError(f"❌ App '{app_label}' not found. Make sure it’s listed in INSTALLED_APPS.")

        self.stdout.write(self.style.MIGRATE_HEADING(f"\n🩺 Repairing app schema for: {app_label}\n"))

        try:
            # Step 2 — Regenerate migrations
            self.stdout.write(self.style.HTTP_INFO(f"🔧 Generating migrations for '{app_label}'..."))
            subprocess.run(
                [sys.executable, "manage.py", "makemigrations", app_label],
                check=True
            )

            # Step 3 — Reset migration history
            self.stdout.write(self.style.HTTP_INFO(f"🧹 Resetting migration history for '{app_label}'..."))
            subprocess.run(
                [sys.executable, "manage.py", "migrate", app_label, "zero", "--fake"],
                check=True
            )

            # Step 4 — Apply migrations safely (fake-initial)
            self.stdout.write(self.style.HTTP_INFO(f"🚀 Applying migrations for '{app_label}' (safe mode)..."))
            subprocess.run(
                [sys.executable, "manage.py", "migrate", app_label, "--fake-initial"],
                check=True
            )

            # Step 5 — List existing DB tables
            self.stdout.write(self.style.HTTP_INFO(f"📋 Verifying database tables for '{app_label}'..."))
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA table_list;")
                tables = [t[1] for t in cursor.fetchall() if app_label in t[1]]
                if tables:
                    self.stdout.write(self.style.HTTP_INFO(f"   Found tables: {', '.join(tables)}"))
                else:
                    self.stdout.write(self.style.WARNING("   ⚠️ No tables found for this app."))

            # Step 6 — Verify model fields vs. DB columns
            self.stdout.write(self.style.HTTP_INFO("\n🔍 Verifying column consistency..."))
            missing_columns = {}
            with connection.cursor() as cursor:
                for model in apps.get_models():
                    if model._meta.app_label != app_label:
                        continue

                    table = model._meta.db_table
                    try:
                        cursor.execute(f"PRAGMA table_info({table});")
                        db_columns = {col[1] for col in cursor.fetchall()}
                        model_fields = {
                            f.column
                            for f in model._meta.get_fields()
                            if hasattr(f, "column") and f.column
                        }
                        missing = model_fields - db_columns
                        if missing:
                            missing_columns[table] = sorted(list(missing))
                    except OperationalError as e:
                        self.stdout.write(self.style.ERROR(f"   ❌ Could not inspect table '{table}': {e}"))

            if missing_columns:
                self.stdout.write(self.style.WARNING("\n⚠️ Missing columns detected:"))
                for table, cols in missing_columns.items():
                    self.stdout.write(self.style.WARNING(f"   • {table}: {', '.join(cols)}"))
                self.stdout.write(self.style.HTTP_INFO("\n💡 Suggested fix:"))
                self.stdout.write(self.style.HTTP_INFO(
                    f"   Run: python manage.py makemigrations {app_label}\n   Then: python manage.py migrate {app_label}"
                ))
            else:
                self.stdout.write(self.style.SUCCESS("\n✅ All database columns are in sync!"))

            self.stdout.write(self.style.SUCCESS(f"\n🎉 Successfully repaired '{app_label}' schema!\n"))

        except OperationalError as e:
            raise CommandError(f"❌ Database operation failed: {e}")
        except subprocess.CalledProcessError as e:
            raise CommandError(f"❌ Command execution failed: {e}")
        except Exception as e:
            raise CommandError(f"⚠️ Unexpected error: {e}")

        self.stdout.write(self.style.MIGRATE_HEADING("🩷 Repair process completed.\n"))
