#!/usr/bin/env python
"""
Script to check for project updates, including:
- Milestone delays
- Project deadlines
- Other automations

This can be run manually or scheduled with cron/Task Scheduler
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelenso.settings')
django.setup()

from django.utils import timezone
from core.models import Project, ProjectMilestone
from core.views import check_delayed_milestones

def main():
    """Main function to check for various project updates"""
    print(f"==== Project Updates Check - {timezone.now()} ====")
    
    # Check for delayed milestones
    print("\n1. Checking for delayed milestones...")
    delayed_count = check_delayed_milestones()
    print(f"   Found {delayed_count} new delayed milestones")
    
    # Check other project conditions as needed
    # Add more checks here in the future
    
    print("\nComplete! All checks finished.")

if __name__ == "__main__":
    main() 