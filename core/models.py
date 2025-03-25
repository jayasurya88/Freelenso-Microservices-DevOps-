from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_freelancer = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    skills = models.CharField(max_length=500, null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    website = models.URLField(max_length=200, null=True, blank=True)
    linkedin = models.URLField(max_length=200, null=True, blank=True)
    github = models.URLField(max_length=200, null=True, blank=True)
    languages = models.CharField(max_length=200, null=True, blank=True)
    education = models.TextField(null=True, blank=True)
    experience = models.TextField(null=True, blank=True)
    availability = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    def is_profile_complete(self):
        if self.is_freelancer:
            # Required fields for freelancers
            required_fields = [
                self.bio,
                self.skills,
                self.hourly_rate,
                self.country,
                self.phone_number,
                self.languages,
                self.education,
                self.experience,
                self.availability
            ]
            return all(field for field in required_fields)
        else:
            # Required fields for clients
            required_fields = [
                self.bio,
                self.country,
                self.phone_number
            ]
            return all(field for field in required_fields)

class Project(models.Model):
    PROJECT_STATUS_CHOICES = [
        ('open', 'Open for Applications'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    DURATION_CHOICES = [
        ('short', 'Less than 1 month'),
        ('medium', '1-3 months'),
        ('long', '3-6 months'),
        ('ongoing', 'Ongoing')
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert')
    ]

    title = models.CharField(max_length=200)
    client = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='posted_projects')
    description = models.TextField()
    required_skills = models.CharField(max_length=500)
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES)
    status = models.CharField(max_length=20, choices=PROJECT_STATUS_CHOICES, default='open')
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateField(null=True, blank=True)
    assigned_freelancer = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_projects')

    # New fields for workspace
    progress = models.IntegerField(default=0)  # Overall progress percentage
    total_milestones = models.IntegerField(default=0)
    completed_milestones = models.IntegerField(default=0)
    last_activity_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    def update_progress(self):
        """Update project progress based on completed milestones"""
        if self.total_milestones > 0:
            self.progress = (self.completed_milestones / self.total_milestones) * 100
        self.save()

    def update_last_activity(self):
        """Update the last activity timestamp"""
        self.last_activity_date = timezone.now()
        self.save()

    class Meta:
        ordering = ['-created_at']

class ProjectAttachment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='project_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.project.title}"

    class Meta:
        ordering = ['-uploaded_at']

class ProjectApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn')
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='applications')
    freelancer = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='project_applications')
    cover_letter = models.TextField()
    proposed_budget = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    estimated_duration = models.CharField(max_length=20, choices=Project.DURATION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Application for {self.project.title} by {self.freelancer.user.username}"

    class Meta:
        ordering = ['-created_at']
        unique_together = ['project', 'freelancer']  # Prevent multiple applications

class ProjectMilestone(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completion_notes = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.project.title}"

    class Meta:
        ordering = ['due_date']

class ProjectActivity(models.Model):
    """Model for tracking project activities"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50, choices=[
        ('milestone_created', 'Milestone Created'),
        ('milestone_completed', 'Milestone Completed'),
        ('milestone_approved', 'Milestone Approved'),
        ('milestone_rejected', 'Milestone Rejected'),
        ('milestone_updated', 'Milestone Updated'),
        ('milestone_deleted', 'Milestone Deleted'),
        ('file_uploaded', 'File Uploaded'),
        ('message_sent', 'Message Sent'),
        ('status_updated', 'Status Updated'),
        ('payment_released', 'Payment Released'),
    ])
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Project Activities'

class ProjectFile(models.Model):
    """Model for project files"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='project_files/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    milestone = models.ForeignKey(ProjectMilestone, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliverable_files')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.file_name

class ChatRoom(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_message_at']
    
    def __str__(self):
        return f"Chat Room for {self.project.title}"

class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    message = models.TextField()
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        # Truncate long messages for display
        short_message = self.message[:30] + "..." if len(self.message) > 30 else self.message
        return f"{short_message} - {self.sender.user.username}"

class ChatParticipant(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['room', 'user']
    
    def __str__(self):
        return f"{self.user.user.username} in {self.room.project.title}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('application', 'Project Application'),
        ('milestone', 'Milestone Update'),
        ('project', 'Project Update'),
        ('payment', 'Payment Update'),
    ]
    
    recipient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.recipient.user.username}"

class Wallet(models.Model):
    """Model for user wallet"""
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(Decimal('0.00'))])
    escrow_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(Decimal('0.00'))])
    currency = models.CharField(max_length=3, default='USD')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.user.username}'s Wallet ({self.balance} {self.currency})"

class Transaction(models.Model):
    """Model for tracking all financial transactions"""
    TRANSACTION_TYPES = [
        ('deposit', 'Wallet Deposit'),
        ('withdrawal', 'Wallet Withdrawal'),
        ('escrow', 'Fund Escrow'),
        ('release', 'Release to Freelancer'),
        ('refund', 'Refund to Client'),
        ('fee', 'Platform Fee'),
    ]

    PAYMENT_METHODS = [
        ('wallet', 'Wallet Balance'),
        ('bank', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('card', 'Credit/Debit Card'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    transaction_id = models.CharField(max_length=100, unique=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    milestone = models.ForeignKey(ProjectMilestone, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True)
    reference_id = models.CharField(max_length=100, blank=True)  # For external payment references
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_type} - {self.amount}"

    def save(self, *args, **kwargs):
        # Generate transaction ID if not provided
        if not self.transaction_id:
            import uuid
            self.transaction_id = f"TRX-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']

class WithdrawalRequest(models.Model):
    """Model for withdrawal requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    WITHDRAWAL_METHODS = [
        ('bank', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('paypal', 'PayPal'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    withdrawal_method = models.CharField(max_length=20, choices=WITHDRAWAL_METHODS)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=30, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    upi_id = models.CharField(max_length=50, blank=True, null=True)
    paypal_email = models.EmailField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    reference_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.wallet.user.user.username}'s withdrawal of {self.amount} ({self.status})"

    class Meta:
        ordering = ['-created_at']

class PaymentMethod(models.Model):
    """Model for storing user payment methods"""
    PAYMENT_METHOD_TYPES = [
        ('bank', 'Bank Account'),
        ('upi', 'UPI'),
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=20, choices=PAYMENT_METHOD_TYPES)
    is_default = models.BooleanField(default=False)
    
    # Bank details
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_holder = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=30, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    
    # UPI details
    upi_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Card details (tokenized or masked)
    card_last_digits = models.CharField(max_length=4, blank=True, null=True)
    card_type = models.CharField(max_length=20, blank=True, null=True)
    card_expiry = models.CharField(max_length=7, blank=True, null=True)
    
    # PayPal details
    paypal_email = models.EmailField(blank=True, null=True)
    
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        method_name = dict(self.PAYMENT_METHOD_TYPES)[self.method_type]
        return f"{self.user.user.username}'s {method_name}"

    class Meta:
        unique_together = [['user', 'method_type', 'account_number'], 
                          ['user', 'method_type', 'upi_id'],
                          ['user', 'method_type', 'card_last_digits', 'card_expiry'],
                          ['user', 'method_type', 'paypal_email']]
