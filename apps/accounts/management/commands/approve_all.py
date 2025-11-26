from django.core.management.base import BaseCommand
from apps.accounts.models import User

class Command(BaseCommand):
    help = "Approve all users"

    def handle(self, *args, **options):
        updated = User.objects.update(is_approved=True)
        self.stdout.write(self.style.SUCCESS(f"Approved {updated} users"))
