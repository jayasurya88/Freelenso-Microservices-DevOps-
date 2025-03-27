from django.contrib import admin
from .models import (
    UserProfile, Project, ProjectApplication, ProjectMilestone, 
    ProjectAttachment, ProjectFile, ProjectActivity, ChatRoom, 
    ChatMessage, ChatParticipant, Notification, Wallet, 
    Transaction, WithdrawalRequest, PaymentMethod
)

# Register models with custom admin classes
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_freelancer', 'is_client', 'country', 'phone_number', 'created_at')
    list_filter = ('is_freelancer', 'is_client', 'country')
    search_fields = ('user__username', 'user__email', 'bio', 'skills')
    date_hierarchy = 'created_at'

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'assigned_freelancer', 'status', 'budget_min', 'budget_max', 'created_at')
    list_filter = ('status', 'experience_level', 'duration', 'category')
    search_fields = ('title', 'description', 'required_skills')
    date_hierarchy = 'created_at'

@admin.register(ProjectApplication)
class ProjectApplicationAdmin(admin.ModelAdmin):
    list_display = ('project', 'freelancer', 'proposed_budget', 'status', 'created_at')
    list_filter = ('status', 'estimated_duration')
    search_fields = ('project__title', 'freelancer__user__username', 'cover_letter')
    date_hierarchy = 'created_at'

@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'amount', 'due_date', 'status')
    list_filter = ('status',)
    search_fields = ('title', 'description', 'project__title')
    date_hierarchy = 'due_date'

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'escrow_balance', 'currency', 'is_active')
    list_filter = ('currency', 'is_active')
    search_fields = ('user__user__username', 'user__user__email')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'wallet', 'amount', 'transaction_type', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'payment_method')
    search_fields = ('transaction_id', 'description', 'wallet__user__user__username')
    date_hierarchy = 'created_at'

@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'amount', 'fee', 'withdrawal_method', 'status', 'created_at')
    list_filter = ('status', 'withdrawal_method')
    search_fields = ('wallet__user__user__username', 'reference_id')
    date_hierarchy = 'created_at'

# Register the rest of the models with default admin
admin.site.register(ProjectAttachment)
admin.site.register(ProjectFile)
admin.site.register(ProjectActivity)
admin.site.register(ChatRoom)
admin.site.register(ChatMessage)
admin.site.register(ChatParticipant)
admin.site.register(Notification)
admin.site.register(PaymentMethod)
