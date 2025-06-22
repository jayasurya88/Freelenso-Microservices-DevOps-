from django.core.management.base import BaseCommand
from django.utils import timezone
from core.views import check_delayed_milestones

class Command(BaseCommand):
    help = 'Check for delayed milestones and update their status'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting milestone delay check...'))
        
        delayed_count = check_delayed_milestones()
        
        self.stdout.write(
            self.style.SUCCESS(f'Completed milestone delay check. {delayed_count} new delays detected.')
        ) 