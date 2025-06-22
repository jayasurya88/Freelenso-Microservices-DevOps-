import os
import django
import sys
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelenso.settings')
django.setup()

from core.models import ProjectMilestone, Wallet, Transaction
from django.db import transaction

def fix_milestone_payment():
    """
    Fix the payment for a milestone that was approved but not paid to the freelancer.
    This is a one-time fix script for the milestone titled 'asd'.
    """
    # Get the milestone
    milestone = ProjectMilestone.objects.filter(title='asd').first()
    
    if not milestone:
        print("Milestone 'asd' not found")
        return
    
    # Check if milestone is already approved
    if milestone.status != 'approved':
        print(f"Milestone is not approved. Current status: {milestone.status}")
        return
    
    # Check if there's already a transaction for this milestone
    existing_transaction = Transaction.objects.filter(
        milestone=milestone,
        transaction_type='release'
    ).exists()
    
    if existing_transaction:
        print("A transaction record already exists for this milestone")
        return
    
    # Get the project and user profiles
    project = milestone.project
    freelancer = project.assigned_freelancer
    
    if not freelancer:
        print("No freelancer assigned to the project")
        return
    
    # Get or create the freelancer's wallet
    freelancer_wallet, created = Wallet.objects.get_or_create(user=freelancer)
    
    # Get the milestone amount
    milestone_amount = Decimal(str(milestone.amount))
    
    # Execute the fix with transaction atomicity
    try:
        with transaction.atomic():
            # Add to freelancer's wallet balance
            freelancer_wallet.balance += milestone_amount
            freelancer_wallet.save()
            
            # Create transaction record for freelancer
            Transaction.objects.create(
                wallet=freelancer_wallet,
                project=project,
                milestone=milestone,
                amount=milestone_amount,
                transaction_type='release',
                payment_method='wallet',
                status='completed',
                description=f'Payment for milestone: {milestone.title}'
            )
            
            print(f"Successfully added {milestone_amount} to {freelancer.user.username}'s wallet")
            print(f"New wallet balance: {freelancer_wallet.balance}")
    
    except Exception as e:
        print(f"Error fixing milestone payment: {str(e)}")

if __name__ == "__main__":
    print("Starting milestone payment fix...")
    fix_milestone_payment()
    print("Completed.") 