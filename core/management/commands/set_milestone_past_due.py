from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Project, ProjectMilestone

class Command(BaseCommand):
    help = 'Set a milestone to past due for testing the delay system'

    def add_arguments(self, parser):
        parser.add_argument('milestone_id', type=int, help='ID of the milestone to set past due')
        parser.add_argument('--days', type=int, default=30, help='Number of days in the past (default: 30)')
        parser.add_argument('--penalty', type=float, default=5.0, help='Penalty percentage per day (default: 5.0)')

    def handle(self, *args, **options):
        milestone_id = options['milestone_id']
        days_past = options['days']
        penalty_per_day = options['penalty']

        try:
            milestone = ProjectMilestone.objects.get(id=milestone_id)
        except ProjectMilestone.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Milestone with ID {milestone_id} does not exist'))
            return

        # Update milestone
        past_date = timezone.now().date() - timedelta(days=days_past)
        original_due_date = milestone.due_date
        original_status = milestone.status

        milestone.due_date = past_date
        milestone.status = 'pending'
        milestone.penalty_per_day = penalty_per_day
        milestone.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Milestone "{milestone.title}" (ID: {milestone.id}) has been updated:\n'
                f'Original due date: {original_due_date} -> New due date: {milestone.due_date}\n'
                f'Original status: {original_status} -> New status: {milestone.status}\n'
                f'Penalty per day: {milestone.penalty_per_day}%\n'
                f'Days past due: {days_past}'
            )
        ) 