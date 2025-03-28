from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Project, ProjectApplication, ProjectMilestone, ProjectAttachment, ProjectFile, ProjectActivity, ChatRoom, ChatMessage, ChatParticipant, Notification, Wallet, Transaction, WithdrawalRequest, PaymentMethod, ProjectReview
from django.contrib import messages
from django.conf import settings
from django.db.models import Q, Sum, Avg, Count
import os
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.paginator import Paginator
from django.utils.text import slugify
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db import transaction

# Create your views here.
def index(request):
    return render(request,'index.html')

def register_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('register')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('register')
        
        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Create profile
        profile = UserProfile.objects.create(
            user=user,
            is_freelancer=user_type == 'freelancer',
            is_client=user_type == 'client'
        )
        
        login(request, user)
        
        # If registering as freelancer, redirect to edit profile
        if user_type == 'freelancer':
            messages.info(request, 'Please complete your freelancer profile information.')
            return redirect('edit_profile')
        
        return redirect('dashboard')
        
    return render(request, 'register.html')

def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Redirect admin users to admin dashboard
            if user.is_superuser:
                return redirect('admin_dashboard')
                
            profile = UserProfile.objects.get(user=user)
            
            if profile.is_freelancer:
                # For freelancers, check profile completion
                if profile.is_profile_complete():
                    return redirect('dashboard')  # Redirect to freelancer dashboard
                else:
                    messages.info(request, 'Please complete your freelancer profile information.')
                    return redirect('edit_profile')
            else:
                # For clients, redirect to dashboard directly
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
            
    return render(request, 'login.html')

def logout_user(request):
    logout(request)
    return redirect('index')

@login_required
def dashboard(request):
    """View for user dashboard"""
    # For admin users, redirect to admin dashboard
    if request.user.is_superuser:
        return redirect('admin_dashboard')
        
    # Get or create user profile (ensures all users have profiles)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if user_profile.is_client:
        # Get client's projects
        context = {
            'profile': user_profile,
        }
        return render(request, 'client_dashboard.html', context)
    else:
        # Get freelancer's projects
        active_projects = user_profile.assigned_projects.exclude(status='completed')
        completed_projects = user_profile.assigned_projects.filter(status='completed')
        
        context = {
            'profile': user_profile,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
        }
        return render(request, 'freelancer_dashboard.html', context)

# Helper function to get user profile safely
def get_user_profile(user):
    """Helper function to get or create user profile while handling superusers"""
    if user.is_superuser:
        # For superusers, get or create an admin profile
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'is_client': False, 'is_freelancer': False}
        )
        return profile
    
    # For regular users, get or create a profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile

@login_required
def profile_view(request):
    # For admin users, redirect to admin dashboard
    if request.user.is_superuser:
        return redirect('admin_dashboard')
        
    profile = get_user_profile(request.user)
    
    # Get reviews received by the user
    reviews = ProjectReview.objects.filter(
        reviewed=profile,
        is_public=True
    ).select_related(
        'project',
        'reviewer',
        'reviewer__user'
    ).order_by('-created_at')
    
    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Get rating distribution
    rating_distribution = list(reviews.values('rating')
                             .annotate(count=Count('id'))
                             .order_by('-rating'))
    
    context = {
        'profile': profile,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'total_reviews': reviews.count(),
        'rating_distribution': rating_distribution,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'profile/view_profile.html', context)

@login_required
def edit_profile(request):
    # For admin users, redirect to admin dashboard
    if request.user.is_superuser:
        return redirect('admin_dashboard')
        
    profile = get_user_profile(request.user)
    
    if request.method == 'POST':
        # Update User model
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        # Update UserProfile model
        profile.bio = request.POST.get('bio', '')
        profile.skills = request.POST.get('skills', '')
        profile.hourly_rate = request.POST.get('hourly_rate') or None
        profile.country = request.POST.get('country', '')
        profile.phone_number = request.POST.get('phone_number', '')
        profile.website = request.POST.get('website', '')
        profile.linkedin = request.POST.get('linkedin', '')
        profile.github = request.POST.get('github', '')
        profile.languages = request.POST.get('languages', '')
        profile.education = request.POST.get('education', '')
        profile.experience = request.POST.get('experience', '')
        profile.availability = request.POST.get('availability', '')
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            try:
                file = request.FILES['profile_picture']
                if file.size > 5 * 1024 * 1024:  # 5MB limit
                    messages.error(request, 'File size too large. Please keep it under 5MB.')
                else:
                    # Delete old profile picture file if it exists
                    if profile.profile_picture:
                        try:
                            old_path = profile.profile_picture.path
                            if os.path.exists(old_path):
                                os.remove(old_path)
                        except Exception as e:
                            pass
                    
                    # Save new profile picture
                    profile.profile_picture = file
                    messages.success(request, 'Profile picture updated successfully!')
            except Exception as e:
                messages.error(request, f'Error uploading profile picture: {str(e)}')
        
        try:
            profile.save()
            messages.success(request, 'Profile updated successfully!')
        except Exception as e:
            messages.error(request, f'Error saving profile: {str(e)}')
        
        return redirect('view_profile')
        
    return render(request, 'profile/edit_profile.html', {
        'profile': profile,
        'user': request.user,
        'MEDIA_URL': settings.MEDIA_URL
    })

@login_required
def project_list(request):
    """View for listing all projects"""
    # Get search parameters
    search_query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    experience_level = request.GET.get('experience_level', '')
    duration = request.GET.get('duration', '')
    
    # Base queryset
    projects = Project.objects.filter(status='open')
    
    # Apply filters
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(required_skills__icontains=search_query)
        )
    if category:
        projects = projects.filter(category=category)
    if experience_level:
        projects = projects.filter(experience_level=experience_level)
    if duration:
        projects = projects.filter(duration=duration)
    
    context = {
        'projects': projects,
        'search_query': search_query,
        'category': category,
        'experience_level': experience_level,
        'duration': duration,
        'categories': Project.objects.values_list('category', flat=True).distinct(),
        'experience_levels': dict(Project.EXPERIENCE_LEVEL_CHOICES),
        'durations': dict(Project.DURATION_CHOICES),
    }
    return render(request, 'projects/project_list.html', context)

@login_required
def project_detail(request, project_id):
    """View for showing project details"""
    project = get_object_or_404(Project, id=project_id)
    user_profile = UserProfile.objects.get(user=request.user)
    
    # Check if user has an active application
    has_active_application = ProjectApplication.objects.filter(
        project=project,
        freelancer=user_profile,
        status='pending'
    ).exists()
    
    # Get application if exists
    application = None
    if has_active_application:
        application = ProjectApplication.objects.get(
            project=project,
            freelancer=user_profile
        )
    
    # Count active (non-withdrawn) applications
    active_applications_count = ProjectApplication.objects.filter(
        project=project,
        status='pending'
    ).count()
    
    # Get all relevant applications for display
    applications = None
    if project.client == user_profile:
        if project.status == 'open':
            # Show all non-withdrawn applications for open projects
            applications = project.applications.exclude(status='withdrawn').order_by('-created_at')
        else:
            # For closed/in-progress projects, only show the accepted application
            applications = project.applications.filter(status='accepted')

    # Debug logging for review conditions
    print(f"Project status: {project.status}")
    print(f"User profile ID: {user_profile.id}")
    print(f"Project client ID: {project.client.id}")
    print(f"Project freelancer ID: {project.assigned_freelancer.id if project.assigned_freelancer else 'None'}")
    print(f"Is user client or freelancer? {user_profile in [project.client, project.assigned_freelancer]}")

    # Check if user can leave a review
    can_review = False
    if project.status == 'completed' and user_profile in [project.client, project.assigned_freelancer]:
        can_review = not ProjectReview.objects.filter(project=project, reviewer=user_profile).exists()
        print(f"Can review: {can_review}")
        if not can_review:
            print("User has already reviewed this project")

    # Get existing review if any
    user_review = None
    if user_profile in [project.client, project.assigned_freelancer]:
        user_review = ProjectReview.objects.filter(project=project, reviewer=user_profile).first()
        if user_review:
            print(f"Found existing review: {user_review.id}")
    
    context = {
        'project': project,
        'has_active_application': has_active_application,
        'application': application,
        'is_owner': project.client == user_profile,
        'active_applications_count': active_applications_count,
        'applications': applications,
        'can_review': can_review,
        'user_review': user_review,
    }
    return render(request, 'projects/project_detail.html', context)

@login_required
def create_project(request):
    """View for creating a new project"""
    if not request.user.userprofile.is_client:
        messages.error(request, "Only clients can create projects.")
        return redirect('dashboard')

    if request.method == 'POST':
        try:
            # Create project
            project = Project.objects.create(
                client=request.user.userprofile,
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                category=request.POST.get('category'),
                budget_min=float(request.POST.get('budget_min')),
                budget_max=float(request.POST.get('budget_max')),
                duration=request.POST.get('duration'),
                deadline=request.POST.get('deadline'),
                required_skills=request.POST.get('skills'),
                experience_level=request.POST.get('experience_level'),
                status='open'
            )

            # Handle file attachments
            files = request.FILES.getlist('attachments')
            for file in files:
                ProjectAttachment.objects.create(
                    project=project,
                    file=file
                )

            # Create milestones
            milestone_titles = request.POST.getlist('milestone_titles[]')
            milestone_amounts = request.POST.getlist('milestone_amounts[]')
            milestone_descriptions = request.POST.getlist('milestone_descriptions[]')
            milestone_due_dates = request.POST.getlist('milestone_due_dates[]')

            milestone_count = 0
            for i in range(len(milestone_titles)):
                if milestone_titles[i] and milestone_amounts[i] and milestone_due_dates[i]:
                    ProjectMilestone.objects.create(
                        project=project,
                        title=milestone_titles[i],
                        amount=float(milestone_amounts[i]),
                        description=milestone_descriptions[i],
                        due_date=milestone_due_dates[i],
                        status='pending'
                    )
                    milestone_count += 1

            # Update project's total milestones count
            project.total_milestones = milestone_count
            project.save()

            messages.success(request, 'Project created successfully!')
            return redirect('project_detail', project_id=project.id)

        except Exception as e:
            messages.error(request, f'Error creating project: {str(e)}')
            return redirect('create_project')

    return render(request, 'projects/create_project.html')

@login_required
def apply_to_project(request, project_id):
    """View for freelancers to apply to projects"""
    project = get_object_or_404(Project, id=project_id)
    user_profile = UserProfile.objects.get(user=request.user)
    
    # Check if user is a freelancer
    if not user_profile.is_freelancer:
        messages.error(request, 'Only freelancers can apply to projects')
        return redirect('project_detail', project_id=project_id)
    
    # Check if project is open
    if project.status != 'open':
        messages.error(request, 'This project is no longer accepting applications')
        return redirect('project_detail', project_id=project_id)
    
    # Check if user has an active application
    has_active_application = ProjectApplication.objects.filter(
        project=project,
        freelancer=user_profile,
        status='pending'
    ).exists()
    
    if has_active_application:
        messages.error(request, 'You have already applied to this project')
        return redirect('project_detail', project_id=project_id)
    
    if request.method == 'POST':
        try:
            # Try to get existing application (including withdrawn ones)
            application, created = ProjectApplication.objects.get_or_create(
                project=project,
                freelancer=user_profile,
                defaults={
                    'cover_letter': request.POST.get('cover_letter'),
                    'proposed_budget': request.POST.get('proposed_budget'),
                    'estimated_duration': request.POST.get('estimated_duration'),
                    'status': 'pending'
                }
            )
            
            # If application existed but was withdrawn, update it
            if not created:
                application.cover_letter = request.POST.get('cover_letter')
                application.proposed_budget = request.POST.get('proposed_budget')
                application.estimated_duration = request.POST.get('estimated_duration')
                application.status = 'pending'
                application.save()
            
            messages.success(request, 'Application submitted successfully!')
            return redirect('project_detail', project_id=project_id)
            
        except Exception as e:
            messages.error(request, f'Error submitting application: {str(e)}')
    
    context = {
        'project': project,
        'duration_choices': Project.DURATION_CHOICES,
    }
    return render(request, 'projects/apply_to_project.html', context)

@login_required
def manage_applications(request, project_id):
    """View for clients to manage project applications"""
    project = get_object_or_404(Project, id=project_id)
    user_profile = UserProfile.objects.get(user=request.user)
    
    # Check if user is a client and is the project owner
    if not user_profile.is_client or project.client != user_profile:
        messages.error(request, 'You do not have permission to manage applications for this project')
        return redirect('project_detail', project_id=project_id)
    
    if request.method == 'POST':
        application_id = request.POST.get('application_id')
        action = request.POST.get('action')
        
        application = get_object_or_404(ProjectApplication, id=application_id, project=project)
        
        if action == 'accept':
            application.status = 'accepted'
            project.status = 'in_progress'
            project.assigned_freelancer = application.freelancer
            project.save()
            # Reject all other applications
            ProjectApplication.objects.filter(project=project).exclude(id=application_id).update(status='rejected')
            messages.success(request, f'Application accepted! Project assigned to {application.freelancer.user.username}')
        elif action == 'reject':
            application.status = 'rejected'
            messages.success(request, 'Application rejected')
        
        application.save()
        return redirect('manage_applications', project_id=project_id)
    
    applications = ProjectApplication.objects.filter(
        project=project
    ).exclude(
        status='withdrawn'
    ).select_related('freelancer', 'freelancer__user')
    
    context = {
        'project': project,
        'applications': applications,
    }
    return render(request, 'projects/manage_applications.html', context)

@login_required
def my_projects(request):
    """View for showing user's projects (both client and freelancer)"""
    user_profile = UserProfile.objects.get(user=request.user)
    
    if user_profile.is_client:
        projects = Project.objects.filter(client=user_profile)
        template = 'projects/client_projects.html'
    else:
        # Get both assigned projects and projects user has applied to
        assigned_projects = Project.objects.filter(assigned_freelancer=user_profile)
        applied_projects = Project.objects.filter(applications__freelancer=user_profile)
        projects = (assigned_projects | applied_projects).distinct()
        template = 'projects/freelancer_projects.html'
    
    context = {
        'projects': projects,
    }
    return render(request, template, context)

@login_required
def delete_project(request, project_id):
    """View for deleting a project"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is the project owner
    if project.client != request.user.userprofile:
        messages.error(request, "You don't have permission to delete this project.")
        return redirect('project_detail', project_id=project_id)
    
    if request.method == 'POST':
        try:
            # Delete all project files
            for attachment in project.attachments.all():
                if attachment.file:
                    if os.path.exists(attachment.file.path):
                        os.remove(attachment.file.path)
            
            # Delete the project (this will cascade delete applications and milestones)
            project.delete()
            
            messages.success(request, 'Project deleted successfully.')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Error deleting project: {str(e)}')
            return redirect('project_detail', project_id=project_id)
    
    return redirect('project_detail', project_id=project_id)

@login_required
def view_freelancer_profile(request, username):
    freelancer = get_object_or_404(UserProfile, user__username=username, is_freelancer=True)
    
    # Get freelancer's projects
    completed_projects = Project.objects.filter(
        assigned_freelancer=freelancer,
        status='completed'
    ).count()
    
    # Get freelancer's applications
    active_applications = ProjectApplication.objects.filter(
        freelancer=freelancer,
        status='pending'
    ).count()

    # Get reviews received by the freelancer
    reviews = ProjectReview.objects.filter(
        reviewed=freelancer,
        is_public=True
    ).select_related(
        'project',
        'reviewer',
        'reviewer__user'
    ).order_by('-created_at')
    
    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'freelancer': freelancer,
        'completed_projects': completed_projects,
        'active_applications': active_applications,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'total_reviews': reviews.count(),
        'MEDIA_URL': settings.MEDIA_URL
    }
    return render(request, 'profile/view_freelancer_profile.html', context)

@login_required
def my_applications(request):
    """View for freelancers to see their applications"""
    user_profile = UserProfile.objects.get(user=request.user)
    
    # If not a freelancer, just redirect to dashboard without error message
    if not user_profile.is_freelancer:
        return redirect('dashboard')
    
    applications = ProjectApplication.objects.filter(
        freelancer=user_profile
    ).select_related('project', 'project__client').order_by('-created_at')
    
    context = {
        'applications': applications,
    }
    return render(request, 'projects/my_applications.html', context)

@login_required
def withdraw_application(request, application_id):
    """View for freelancers to withdraw their applications"""
    application = get_object_or_404(ProjectApplication, id=application_id)
    user_profile = UserProfile.objects.get(user=request.user)
    
    if application.freelancer != user_profile:
        messages.error(request, 'You do not have permission to withdraw this application')
        return redirect('my_applications')
    
    if application.status != 'pending':
        messages.error(request, 'You can only withdraw pending applications')
        return redirect('my_applications')
    
    if request.method == 'POST':
        application.status = 'withdrawn'
        application.save()
        messages.success(request, 'Application withdrawn successfully')
    
    return redirect('my_applications')

@login_required
def project_workspace(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        user_profile = request.user.userprofile
        
        # Check if user has access to this project
        if not (project.client == user_profile or project.assigned_freelancer == user_profile):
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        
        # Get project files
        project_files = ProjectFile.objects.filter(project=project).order_by('-uploaded_at')
        
        # Get project activities
        activities = ProjectActivity.objects.filter(project=project).order_by('-created_at')[:10]
        
        context = {
            'project': project,
            'project_files': project_files,
            'activities': activities,
            'is_client': project.client == user_profile,
            'is_freelancer': project.assigned_freelancer == user_profile
        }
        
        return render(request, 'projects/workspace.html', context)
        
    except Project.DoesNotExist:
        messages.error(request, 'Project not found')
        return redirect('dashboard')

@login_required
def upload_project_file(request, project_id):
    """View for uploading project files"""
    if request.method != 'POST':
        return redirect('project_workspace', project_id=project_id)
        
    project = get_object_or_404(Project, id=project_id)
    user_profile = UserProfile.objects.get(user=request.user)
    
    # Check if user has access to this project
    if not (project.client == user_profile or project.assigned_freelancer == user_profile):
        messages.error(request, 'You do not have permission to upload files to this project')
        return redirect('dashboard')
    
    if 'file' in request.FILES:
        file = request.FILES['file']
        
        # Create project file
        project_file = ProjectFile.objects.create(
            project=project,
            uploaded_by=request.user,
            file=file,
            file_name=file.name,
            file_type=file.content_type
        )
        
        # Create activity record
        ProjectActivity.objects.create(
            project=project,
            user=request.user,
            activity_type='file_uploaded',
            description=f'Uploaded file: {file.name}'
        )
        
        # Update project last activity
        project.update_last_activity()
        
        messages.success(request, 'File uploaded successfully')
    else:
        messages.error(request, 'No file was provided')
    
    return redirect('project_workspace', project_id=project_id)

@login_required
def chat_room(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    user_profile = request.user.userprofile
    
    # Check if user has access to this project
    if user_profile != project.client and user_profile != project.assigned_freelancer:
        messages.error(request, "You don't have access to this chat room.")
        return redirect('project_workspace', project_id=project_id)
    
    # Get or create chat room
    chat_room, created = ChatRoom.objects.get_or_create(project=project)
    
    # Get messages, excluding ones that match the pattern
    messages_list = ChatMessage.objects.filter(room=chat_room).exclude(
        Q(message__contains=' - client') | 
        Q(message__contains=' - freelancer')
    ).order_by('created_at')
    
    # Mark messages as read
    ChatMessage.objects.filter(
        room=chat_room,
        sender__in=[project.client, project.assigned_freelancer],
        sender__user__is_active=True,
        is_read=False
    ).exclude(sender=user_profile).update(is_read=True)
    
    return render(request, 'chat/chat_room.html', {
        'project': project,
        'messages': messages_list,
        'chat_room': chat_room
    })

@login_required
def send_message(request, project_id):
    """Send a message to the chat room"""
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id)
        
        # Check if the user has access to the project
        if request.user.userprofile != project.client and request.user.userprofile != project.assigned_freelancer:
            return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
        
        message_text = request.POST.get('message', '').strip()
        file = request.FILES.get('file', None)
        
        if not message_text and not file:
            return JsonResponse({'status': 'error', 'message': 'Message cannot be empty'}, status=400)
        
        # Get or create chat room
        chat_room, created = ChatRoom.objects.get_or_create(project=project)
        
        # Save message
        chat_message = ChatMessage.objects.create(
            room=chat_room,
            sender=request.user.userprofile,
            message=message_text,
            file=file
        )
        
        # Create a notification for the recipient
        recipient = project.client if request.user.userprofile == project.assigned_freelancer else project.assigned_freelancer
        if recipient:
            create_notification(
                recipient=recipient,
                notification_type='message',
                message=f"New message from {request.user.username} in project '{project.title}'",
                sender=request.user.userprofile,
                project=project
            )
        
        # Update last message timestamp for the room
        chat_room.save()  # This will update the auto_now field
        
        response_data = {
            'id': chat_message.id,
            'message': chat_message.message,
            'sender_id': chat_message.sender.id,
            'sender_name': chat_message.sender.user.username,
            'created_at': chat_message.created_at.strftime('%b %d, %Y %H:%M'),
            'file_url': chat_message.file.url if chat_message.file else None
        }
        
        return JsonResponse(response_data)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def get_messages(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    user_profile = request.user.userprofile
    
    # Check if user has access to this project
    if user_profile != project.client and user_profile != project.assigned_freelancer:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get chat room
    chat_room = get_object_or_404(ChatRoom, project=project)
    
    # Get messages, exclude improperly formatted ones
    messages_list = ChatMessage.objects.filter(room=chat_room).exclude(
        Q(message__contains=' - client') | 
        Q(message__contains=' - freelancer')
    ).order_by('created_at')
    
    # Mark messages as read
    ChatMessage.objects.filter(
        room=chat_room,
        sender__in=[project.client, project.assigned_freelancer],
        sender__user__is_active=True,
        is_read=False
    ).exclude(sender=user_profile).update(is_read=True)
    
    messages_data = [{
        'id': msg.id,
        'message': msg.message,
        'sender_id': msg.sender.id,
        'sender_name': msg.sender.user.username,
        'created_at': msg.created_at.strftime('%b %d, %Y %H:%M'),
        'file_url': msg.file.url if msg.file else None
    } for msg in messages_list]
    
    return JsonResponse({'messages': messages_data})

@login_required
def mark_message_read(request, project_id, message_id):
    project = get_object_or_404(Project, id=project_id)
    user_profile = request.user.userprofile
    
    # Check if user has access to this project
    if user_profile != project.client and user_profile != project.assigned_freelancer:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get message
    message = get_object_or_404(ChatMessage, id=message_id, room__project=project)
    
    # Mark message as read
    if message.sender != user_profile:
        message.is_read = True
        message.save()
    
    return JsonResponse({'status': 'success'})

@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Check if the user is the client who created the project
    if project.client != request.user:
        messages.error(request, "You don't have permission to edit this project.")
        return redirect('project_detail', project_id=project_id)
    
    if request.method == 'POST':
        # Update project fields
        project.title = request.POST.get('title')
        project.description = request.POST.get('description')
        project.required_skills = request.POST.get('required_skills')
        project.budget_min = request.POST.get('budget_min')
        project.budget_max = request.POST.get('budget_max')
        project.duration = request.POST.get('duration')
        project.experience_level = request.POST.get('experience_level')
        project.save()
        
        messages.success(request, 'Project updated successfully!')
        return redirect('project_detail', project_id=project_id)
    
    context = {
        'project': project,
    }
    return render(request, 'projects/edit_project.html', context)

@login_required
def notifications(request):
    """View to display user notifications"""
    user_profile = request.user.userprofile
    notifications = Notification.objects.filter(recipient=user_profile)
    
    # Mark all as read if specified
    if request.GET.get('mark_read'):
        notifications.update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'notifications/notification_list.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user.userprofile)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

def get_unread_notifications_count(user_profile):
    """Helper function to get unread notification count"""
    return Notification.objects.filter(recipient=user_profile, is_read=False).count()

# Update context processor to add notifications to all views
def add_notifications_to_context(request):
    """Add unread notifications count to context for all views"""
    if request.user.is_authenticated:
        # Handle superusers separately since they might not have a UserProfile
        if request.user.is_superuser:
            return {'unread_notifications_count': 0}
            
        try:
            # Get or create a UserProfile for the user to ensure it exists
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            unread_count = get_unread_notifications_count(user_profile)
            return {'unread_notifications_count': unread_count}
        except Exception as e:
            print(f"Error getting notifications count: {str(e)}")
            return {'unread_notifications_count': 0}
    return {'unread_notifications_count': 0}

# Helper function to create a notification
def create_notification(recipient, notification_type, message, sender=None, project=None):
    """Create a new notification"""
    notification = Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        project=project,
        message=message
    )
    return notification

@login_required
def message_list(request):
    """View to display a list of all chat rooms for a user"""
    # Redirect superusers to admin dashboard
    if request.user.is_superuser:
        return redirect('admin_dashboard')
        
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get all chat rooms where the user is client or freelancer
    chat_rooms = ChatRoom.objects.filter(
        Q(project__client=user_profile) | Q(project__assigned_freelancer=user_profile)
    ).select_related('project', 'project__client', 'project__assigned_freelancer').order_by('-last_message_at')
    
    # Enhance chat rooms with last message and unread count
    for room in chat_rooms:
        # Get last message
        last_message = ChatMessage.objects.filter(room=room).order_by('-created_at').first()
        room.last_message = last_message
        
        # Count unread messages
        room.unread_count = ChatMessage.objects.filter(
            room=room,
            is_read=False
        ).exclude(sender=user_profile).count()
    
    context = {
        'chat_rooms': chat_rooms,
    }
    return render(request, 'chat/message_list.html', context)

@login_required
def cleanup_messages(request):
    """Administrative view to automatically clean up improperly formatted messages"""
    # Only superusers or staff can use this function
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('message_list')
    
    # Find messages that match the pattern (containing ' - client' or ' - freelancer')
    improper_messages = ChatMessage.objects.filter(
        Q(message__contains=' - client') | 
        Q(message__contains=' - freelancer')
    )
    
    # Delete the improper messages immediately
    count = improper_messages.count()
    improper_messages.delete()
    
    messages.success(request, f"Successfully deleted {count} improperly formatted messages.")
    return redirect('message_list')

@login_required
def create_milestone(request, project_id):
    """Add a new milestone to an existing project"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is the client
    if request.user.userprofile != project.client:
        messages.error(request, "Only the project owner can add milestones.")
        return redirect('project_detail', project_id=project_id)
    
    # Check if project is in appropriate status
    if project.status not in ['open', 'in_progress']:
        messages.error(request, "Cannot add milestones to completed or cancelled projects.")
        return redirect('project_detail', project_id=project_id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        due_date = request.POST.get('due_date')
        
        if title and amount and due_date:
            milestone = ProjectMilestone.objects.create(
                project=project,
                title=title,
                description=description,
                amount=float(amount),
                due_date=due_date
            )
            
            # Update project total milestones
            project.total_milestones += 1
            project.save()
            project.update_progress()
            
            # Record activity
            ProjectActivity.objects.create(
                project=project,
                user=request.user,
                activity_type='milestone_created',
                description=f"Added milestone: {title}"
            )
            
            # Create notification for freelancer if assigned
            if project.assigned_freelancer:
                create_notification(
                    recipient=project.assigned_freelancer,
                    notification_type='milestone',
                    message=f"New milestone added to project '{project.title}': {title}",
                    sender=request.user.userprofile,
                    project=project
                )
            
            messages.success(request, "Milestone added successfully.")
            # Add a message to inform client about funding the milestone
            messages.info(request, f"Please fund the milestone to release payment to the freelancer when completed. Click 'Fund' next to the milestone.")
            
            return redirect('project_milestones', project_id=project_id)
    
    return render(request, 'projects/milestone_form.html', {
        'project': project,
        'action': 'Create'
    })

@login_required
def edit_milestone(request, project_id, milestone_id):
    """Edit an existing milestone"""
    project = get_object_or_404(Project, id=project_id)
    milestone = get_object_or_404(ProjectMilestone, id=milestone_id, project=project)
    
    # Check if user is the client
    if request.user.userprofile != project.client:
        messages.error(request, "Only the project owner can edit milestones.")
        return redirect('project_milestones', project_id=project_id)
    
    # Check if milestone can be edited (only pending ones)
    if milestone.status != 'pending':
        messages.error(request, "Cannot edit milestones that are already completed or approved.")
        return redirect('project_milestones', project_id=project_id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        due_date = request.POST.get('due_date')
        
        if title and amount and due_date:
            milestone.title = title
            milestone.description = description
            milestone.amount = float(amount)
            milestone.due_date = due_date
            milestone.save()
            
            # Record activity
            ProjectActivity.objects.create(
                project=project,
                user=request.user,
                activity_type='milestone_updated',
                description=f"Updated milestone: {title}"
            )
            
            # Create notification for freelancer if assigned
            if project.assigned_freelancer:
                create_notification(
                    recipient=project.assigned_freelancer,
                    notification_type='milestone',
                    message=f"Milestone updated in project '{project.title}': {title}",
                    sender=request.user.userprofile,
                    project=project
                )
            
            messages.success(request, "Milestone updated successfully.")
            return redirect('project_milestones', project_id=project_id)
    
    return render(request, 'projects/milestone_form.html', {
        'project': project,
        'milestone': milestone,
        'action': 'Edit'
    })

@login_required
def delete_milestone(request, project_id, milestone_id):
    """Delete a milestone"""
    project = get_object_or_404(Project, id=project_id)
    milestone = get_object_or_404(ProjectMilestone, id=milestone_id, project=project)
    
    # Check if user is the client
    if request.user.userprofile != project.client:
        messages.error(request, "Only the project owner can delete milestones.")
        return redirect('project_milestones', project_id=project_id)
    
    # Check if milestone can be deleted (only pending ones)
    if milestone.status != 'pending':
        messages.error(request, "Cannot delete milestones that are already completed or approved.")
        return redirect('project_milestones', project_id=project_id)
    
    if request.method == 'POST' and request.POST.get('confirm_delete') == 'yes':
        milestone_title = milestone.title
        
        # Reduce total milestones count
        project.total_milestones -= 1
        if project.total_milestones < 0:
            project.total_milestones = 0
        project.save()
        project.update_progress()
        
        # Delete the milestone
        milestone.delete()
        
        # Record activity
        ProjectActivity.objects.create(
            project=project,
            user=request.user,
            activity_type='milestone_deleted',
            description=f"Removed milestone: {milestone_title}"
        )
        
        messages.success(request, "Milestone deleted successfully.")
        return redirect('project_milestones', project_id=project_id)
    
    return render(request, 'projects/confirm_delete_milestone.html', {
        'project': project,
        'milestone': milestone
    })

@login_required
def project_milestones(request, project_id):
    """View all milestones for a project"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user has access to this project
    if request.user.userprofile != project.client and request.user.userprofile != project.assigned_freelancer:
        messages.error(request, "You don't have access to this project.")
        return redirect('dashboard')
    
    milestones = project.milestones.all().order_by('due_date')
    
    is_client = request.user.userprofile == project.client
    is_freelancer = request.user.userprofile == project.assigned_freelancer
    
    return render(request, 'projects/milestones.html', {
        'project': project,
        'milestones': milestones,
        'is_client': is_client,
        'is_freelancer': is_freelancer
    })

@login_required
def complete_milestone(request, project_id, milestone_id):
    """Mark a milestone as completed (by freelancer)"""
    project = get_object_or_404(Project, id=project_id)
    milestone = get_object_or_404(ProjectMilestone, id=milestone_id, project=project)
    
    # Check if user is the assigned freelancer
    if request.user.userprofile != project.assigned_freelancer:
        messages.error(request, "Only the assigned freelancer can mark milestones as completed.")
        return redirect('project_milestones', project_id=project_id)
    
    # Check if milestone is in pending or funded status
    if milestone.status not in ['pending', 'funded']:
        messages.error(request, "This milestone is already completed or approved.")
        return redirect('project_milestones', project_id=project_id)
    
    # If milestone is in pending status, check if it should be funded first
    if milestone.status == 'pending':
        messages.warning(request, "This milestone hasn't been funded by the client yet. Please contact the client to fund the milestone before completing it.")
        return redirect('project_milestones', project_id=project_id)
    
    if request.method == 'POST':
        # Get form data
        completion_notes = request.POST.get('completion_notes', '')
        
        # Update milestone status and add completion notes
        milestone.status = 'completed'
        milestone.completion_notes = completion_notes
        milestone.completed_at = timezone.now()
        milestone.save()
        
        # Handle file uploads
        files = request.FILES.getlist('deliverable_files')
        for file in files:
            ProjectFile.objects.create(
                project=project,
                uploaded_by=request.user,
                file=file,
                file_name=file.name,
                file_type=file.content_type,
                description=f"Milestone completion: {milestone.title}",
                milestone=milestone
            )
        
        # Record activity
        ProjectActivity.objects.create(
            project=project,
            user=request.user,
            activity_type='milestone_completed',
            description=f"Marked milestone as completed: {milestone.title}"
        )
        
        # Create notification for client
        create_notification(
            recipient=project.client,
            notification_type='milestone',
            message=f"Milestone marked as completed in project '{project.title}': {milestone.title}",
            sender=request.user.userprofile,
            project=project
        )
        
        messages.success(request, "Milestone marked as completed. Waiting for client approval.")
        return redirect('project_milestones', project_id=project_id)
    
    return render(request, 'projects/complete_milestone.html', {
        'project': project,
        'milestone': milestone
    })

@login_required
def approve_milestone(request, project_id, milestone_id):
    project = get_object_or_404(Project, id=project_id)
    milestone = get_object_or_404(ProjectMilestone, id=milestone_id, project=project)
    
    # Verify user is the project client and milestone is completed
    if request.user.userprofile != project.client or milestone.status != 'completed':
        messages.error(request, 'You are not authorized to approve this milestone.')
        return redirect('project_detail', project_id=project_id)
    
    try:
        with transaction.atomic():
            # Update milestone status
            milestone.status = 'approved'
            milestone.save()
            
            # Increment completed milestones count
            project.completed_milestones += 1
            project.save()
            
            # Check if project is completed
            if project.completed_milestones == project.total_milestones:
                project.status = 'completed'
                project.save()
                
                # Create notifications for both client and freelancer
                Notification.objects.create(
                    recipient=project.client.user,
                    title='Project Completed',
                    message=f'Project "{project.title}" has been completed. You can now leave a review.',
                    notification_type='project_completed'
                )
                
                Notification.objects.create(
                    recipient=project.assigned_freelancer.user,
                    title='Project Completed',
                    message=f'Project "{project.title}" has been completed. You can now leave a review.',
                    notification_type='project_completed'
                )
                
                # Handle wallet transactions
                platform_fee = project.total_budget * Decimal('0.10')  # 10% platform fee
                freelancer_amount = project.total_budget - platform_fee
                
                # Create release transaction for client
                Transaction.objects.create(
                    user=project.client.user,
                    amount=-project.total_budget,
                    transaction_type='release',
                    description=f'Released payment for project: {project.title}',
                    status='completed'
                )
                
                # Create receipt transaction for freelancer
                Transaction.objects.create(
                    user=project.assigned_freelancer.user,
                    amount=freelancer_amount,
                    transaction_type='receipt',
                    description=f'Received payment for project: {project.title}',
                    status='completed'
                )
                
                # Create platform fee transaction
                Transaction.objects.create(
                    user=User.objects.get(username='admin'),  # Assuming admin user exists
                    amount=platform_fee,
                    transaction_type='platform_fee',
                    description=f'Platform fee for project: {project.title}',
                    status='completed'
                )
                
                # Record activity
                ProjectActivity.objects.create(
                    project=project,
                    user=request.user,
                    activity_type='milestone_approved',
                    description=f'Project completed - All milestones approved'
                )
                
                messages.success(request, 'Project completed successfully! You can now leave a review.')
            else:
                messages.success(request, 'Milestone approved successfully!')
            
            return redirect('project_workspace', project_id=project_id)
            
    except Exception as e:
        messages.error(request, f'Error approving milestone: {str(e)}')
        return redirect('project_detail', project_id=project_id)

@login_required
def reject_milestone(request, project_id, milestone_id):
    """Reject a completed milestone (by client)"""
    project = get_object_or_404(Project, id=project_id)
    milestone = get_object_or_404(ProjectMilestone, id=milestone_id, project=project)
    
    # Check if user is the client
    if request.user.userprofile != project.client:
        messages.error(request, "Only the project owner can reject milestones.")
        return redirect('project_milestones', project_id=project_id)
    
    # Check if milestone is in completed status
    if milestone.status != 'completed':
        messages.error(request, "Only completed milestones can be rejected.")
        return redirect('project_milestones', project_id=project_id)
    
    # Get deliverable files for this milestone
    deliverable_files = ProjectFile.objects.filter(project=project, milestone=milestone)
    
    if request.method == 'POST':
        feedback = request.POST.get('feedback', '')
        
        # Update milestone status
        milestone.status = 'rejected'
        milestone.feedback = feedback
        milestone.save()
        
        # Record activity
        ProjectActivity.objects.create(
            project=project,
            user=request.user,
            activity_type='milestone_rejected',
            description=f"Rejected milestone: {milestone.title}"
        )
        
        # Create notification for freelancer
        create_notification(
            recipient=project.assigned_freelancer,
            notification_type='milestone',
            message=f"Milestone rejected in project '{project.title}': {milestone.title}. Feedback: {feedback}",
            sender=request.user.userprofile,
            project=project
        )
        
        messages.success(request, "Milestone rejected. The freelancer has been notified.")
        return redirect('project_milestones', project_id=project_id)
    
    return render(request, 'projects/reject_milestone.html', {
        'project': project,
        'milestone': milestone,
        'deliverable_files': deliverable_files
    })

# Wallet Views
@login_required
def wallet_dashboard(request):
    """
    Display wallet dashboard with balance and recent transactions
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    # Create wallet if it doesn't exist
    wallet, created = Wallet.objects.get_or_create(
        user=user_profile,
        defaults={'currency': 'USD'}
    )
    
    # Get recent transactions
    recent_transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')[:5]
    
    # Get active withdrawal requests
    active_withdrawals = WithdrawalRequest.objects.filter(
        wallet=wallet, 
        status__in=['pending', 'processing']
    )
    
    # Calculate total funds (balance + escrow)
    total_funds = wallet.balance + wallet.escrow_balance
    
    context = {
        'wallet': wallet,
        'recent_transactions': recent_transactions,
        'active_withdrawals': active_withdrawals,
        'total_funds': total_funds,
    }
    
    if user_profile.is_freelancer:
        # Get project-specific stats for freelancers
        completed_milestones = ProjectMilestone.objects.filter(
            project__assigned_freelancer=user_profile,
            status='approved'
        )
        earnings_this_month = completed_milestones.filter(
            completed_at__month=timezone.now().month,
            completed_at__year=timezone.now().year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context.update({
            'earnings_this_month': earnings_this_month,
            'completed_milestones_count': completed_milestones.count(),
        })
    
    if user_profile.is_client:
        # Get project-specific stats for clients
        active_projects = Project.objects.filter(
            client=user_profile,
            status='in_progress'
        )
        total_escrowed = wallet.escrow_balance
        
        context.update({
            'active_projects_count': active_projects.count(),
            'total_escrowed': total_escrowed,
        })
    
    return render(request, 'wallet/dashboard.html', context)

@login_required
def wallet_transactions(request):
    """
    Display all wallet transactions with filtering
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)
    wallet = get_object_or_404(Wallet, user=user_profile)
    
    transaction_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    
    transactions = Transaction.objects.filter(wallet=wallet)
    
    # Apply filters
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if status:
        transactions = transactions.filter(status=status)
    
    # Pagination
    paginator = Paginator(transactions, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'wallet': wallet,
        'page_obj': page_obj,
        'transaction_type': transaction_type,
        'status': status,
        'transaction_types': Transaction.TRANSACTION_TYPES,
        'status_choices': Transaction.STATUS_CHOICES,
    }
    
    return render(request, 'wallet/transactions.html', context)

@login_required
def wallet_escrow_records(request):
    """
    Display all escrow records for the current user
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)
    wallet = get_object_or_404(Wallet, user=user_profile)
    
    # Get all escrow transactions
    escrow_transactions = Transaction.objects.filter(
        wallet=wallet,
        transaction_type='escrow',
        status='completed'
    ).select_related('project', 'milestone').order_by('-created_at')
    
    # Get active project milestones with escrow
    if user_profile.is_client:
        # For clients, show milestones they're funding
        active_escrows = []
        for transaction in escrow_transactions:
            if transaction.milestone and transaction.milestone.status in ['funded', 'completed']:
                # Only include milestones that haven't been approved yet
                if transaction.milestone.status != 'approved':
                    active_escrows.append({
                        'transaction': transaction,
                        'project': transaction.project,
                        'milestone': transaction.milestone,
                        'amount': transaction.amount,
                        'date': transaction.created_at,
                        'status': transaction.milestone.status
                    })
    elif user_profile.is_freelancer:
        # For freelancers, show milestones funded for their projects
        active_escrows = []
        freelancer_projects = Project.objects.filter(assigned_freelancer=user_profile)
        
        for project in freelancer_projects:
            client_wallet = get_object_or_404(Wallet, user=project.client)
            project_escrows = Transaction.objects.filter(
                wallet=client_wallet,
                project=project,
                transaction_type='escrow',
                status='completed'
            ).select_related('milestone')
            
            for transaction in project_escrows:
                if transaction.milestone and transaction.milestone.status in ['funded', 'completed']:
                    active_escrows.append({
                        'transaction': transaction,
                        'project': project,
                        'milestone': transaction.milestone,
                        'amount': transaction.amount,
                        'date': transaction.created_at,
                        'status': transaction.milestone.status
                    })
    
    # Pagination
    paginator = Paginator(active_escrows, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'wallet': wallet,
        'page_obj': page_obj,
        'is_client': user_profile.is_client,
        'is_freelancer': user_profile.is_freelancer,
        'total_escrow': wallet.escrow_balance if user_profile.is_client else sum(escrow['amount'] for escrow in active_escrows)
    }
    
    return render(request, 'wallet/escrow_records.html', context)

@login_required
def wallet_deposit(request):
    """
    Handle wallet deposit process
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)
    wallet, created = Wallet.objects.get_or_create(user=user_profile)
    
    # Get user's payment methods
    payment_methods = PaymentMethod.objects.filter(user=user_profile)
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        payment_method_id = request.POST.get('payment_method')
        
        if amount <= 0:
            messages.error(request, 'Please enter a valid amount.')
            return redirect('wallet_deposit')
        
        # In a real implementation, you would integrate with a payment gateway here
        # For demonstration, we'll create a pending transaction
        transaction = Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='deposit',
            payment_method='upi',  # Default to UPI for this example
            status='pending',
            description=f'Deposit of {amount} to wallet',
        )
        
        # Redirect to confirmation page
        return redirect('wallet_deposit_confirm')
    
    context = {
        'wallet': wallet,
        'payment_methods': payment_methods,
    }
    
    return render(request, 'wallet/deposit.html', context)

@login_required
def wallet_deposit_confirm(request):
    """
    Confirm wallet deposit and process payment
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)
    wallet = get_object_or_404(Wallet, user=user_profile)
    
    # Get latest pending deposit transaction
    transaction = Transaction.objects.filter(
        wallet=wallet,
        transaction_type='deposit',
        status='pending'
    ).order_by('-created_at').first()
    
    if not transaction:
        messages.error(request, 'No pending deposit found.')
        return redirect('wallet_dashboard')
    
    if request.method == 'POST':
        # In a real implementation, this would verify the payment was received
        # For demonstration, we'll just mark it as completed and add to balance
        
        # Update transaction status
        transaction.status = 'completed'
        transaction.save()
        
        # Update wallet balance
        wallet.balance += transaction.amount
        wallet.updated_at = timezone.now()
        wallet.save()
        
        messages.success(request, f'Successfully deposited {transaction.amount} to your wallet.')
        return redirect('wallet_dashboard')
    
    context = {
        'wallet': wallet,
        'transaction': transaction,
    }
    
    return render(request, 'wallet/deposit_confirm.html', context)

@login_required
def wallet_withdraw(request):
    """
    Handle withdrawal requests from wallet
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)
    wallet = get_object_or_404(Wallet, user=user_profile)
    
    # Get user's payment methods
    payment_methods = PaymentMethod.objects.filter(user=user_profile)
    default_method = payment_methods.filter(is_default=True).first()
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        withdrawal_method = request.POST.get('withdrawal_method')
        payment_method_id = request.POST.get('payment_method')
        
        # Validate withdrawal amount
        if amount <= 0:
            messages.error(request, 'Please enter a valid amount.')
            return redirect('wallet_withdraw')
        
        if amount > wallet.balance:
            messages.error(request, 'Insufficient balance for this withdrawal.')
            return redirect('wallet_withdraw')
        
        # Calculate fee (if any)
        fee = amount * Decimal('0.01')  # 1% fee as an example
        net_amount = amount - fee
        
        if net_amount <= 0:
            messages.error(request, 'Withdrawal amount is too small after fees.')
            return redirect('wallet_withdraw')
        
        # Create withdrawal request
        withdrawal = WithdrawalRequest.objects.create(
            wallet=wallet,
            amount=amount,
            fee=fee,
            withdrawal_method=withdrawal_method,
            status='pending',
        )
        
        # Add payment method details if available
        if payment_method_id:
            method = PaymentMethod.objects.get(id=payment_method_id)
            if method.method_type == 'bank':
                withdrawal.bank_name = method.bank_name
                withdrawal.account_number = method.account_number
                withdrawal.ifsc_code = method.ifsc_code
            elif method.method_type == 'upi':
                withdrawal.upi_id = method.upi_id
            elif method.method_type == 'paypal':
                withdrawal.paypal_email = method.paypal_email
            withdrawal.save()
        
        # Deduct from wallet balance
        wallet.balance -= amount
        wallet.save()
        
        # Create transaction record
        Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            fee_amount=fee,
            transaction_type='withdrawal',
            payment_method=withdrawal_method,
            status='pending',
            description=f'Withdrawal of {amount} from wallet',
            reference_id=withdrawal.id
        )
        
        messages.success(request, f'Withdrawal request of {amount} submitted successfully. It will be processed within 1-3 business days.')
        return redirect('wallet_dashboard')
    
    context = {
        'wallet': wallet,
        'payment_methods': payment_methods,
        'default_method': default_method,
        'min_withdrawal': 10.00,  # Minimum withdrawal amount
        'withdrawal_methods': WithdrawalRequest.WITHDRAWAL_METHODS,
    }
    
    return render(request, 'wallet/withdraw.html', context)

@login_required
def payment_methods(request):
    """
    Display and manage user's payment methods
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)
    payment_methods = PaymentMethod.objects.filter(user=user_profile)
    
    context = {
        'payment_methods': payment_methods,
    }
    
    return render(request, 'wallet/payment_methods.html', context)

@login_required
def add_payment_method(request):
    """
    Add a new payment method
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        method_type = request.POST.get('method_type')
        is_default = request.POST.get('is_default') == 'on'
        
        # If setting as default, clear other defaults
        if is_default:
            PaymentMethod.objects.filter(user=user_profile, is_default=True).update(is_default=False)
        
        # Create payment method based on type
        method = PaymentMethod(
            user=user_profile,
            method_type=method_type,
            is_default=is_default
        )
        
        if method_type == 'bank':
            method.bank_name = request.POST.get('bank_name')
            method.account_holder = request.POST.get('account_holder')
            method.account_number = request.POST.get('account_number')
            method.ifsc_code = request.POST.get('ifsc_code')
        elif method_type == 'upi':
            method.upi_id = request.POST.get('upi_id')
        elif method_type == 'card':
            method.card_last_digits = request.POST.get('card_number')[-4:] if request.POST.get('card_number') else ''
            method.card_type = request.POST.get('card_type')
            method.card_expiry = request.POST.get('card_expiry')
        elif method_type == 'paypal':
            method.paypal_email = request.POST.get('paypal_email')
        
        method.save()
        messages.success(request, 'Payment method added successfully.')
        return redirect('payment_methods')
    
    context = {
        'method_types': PaymentMethod.PAYMENT_METHOD_TYPES,
    }
    
    return render(request, 'wallet/add_payment_method.html', context)

@login_required
def delete_payment_method(request, method_id):
    """
    Delete a payment method
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)
    payment_method = get_object_or_404(PaymentMethod, id=method_id, user=user_profile)
    
    if request.method == 'POST':
        # Check if it's the default method
        if payment_method.is_default:
            # Find another method to make default if available
            alternate_method = PaymentMethod.objects.filter(user=user_profile).exclude(id=method_id).first()
            if alternate_method:
                alternate_method.is_default = True
                alternate_method.save()
        
        payment_method.delete()
        messages.success(request, 'Payment method deleted successfully.')
        return redirect('payment_methods')
    
    context = {
        'payment_method': payment_method,
    }
    
    return render(request, 'wallet/delete_payment_method.html', context)

@login_required
def set_default_payment_method(request, method_id):
    """
    Set a payment method as default
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)
    payment_method = get_object_or_404(PaymentMethod, id=method_id, user=user_profile)
    
    # Clear existing defaults
    PaymentMethod.objects.filter(user=user_profile, is_default=True).update(is_default=False)
    
    # Set new default
    payment_method.is_default = True
    payment_method.save()
    
    messages.success(request, f'{payment_method} set as your default payment method.')
    return redirect('payment_methods')

@login_required
def fund_milestone(request, project_id, milestone_id):
    """
    Fund a project milestone from client wallet (escrow)
    """
    # Verify user is the project client
    user_profile = get_object_or_404(UserProfile, user=request.user)
    project = get_object_or_404(Project, id=project_id, client=user_profile)
    milestone = get_object_or_404(ProjectMilestone, id=milestone_id, project=project)
    
    # Get client wallet
    wallet, created = Wallet.objects.get_or_create(user=user_profile)
    
    if milestone.status != 'pending':
        messages.error(request, 'This milestone has already been funded or completed.')
        return redirect('project_milestones', project_id=project.id)
    
    if request.method == 'POST':
        # Check if client has enough balance
        if wallet.balance < milestone.amount:
            messages.error(request, f'Insufficient wallet balance. Please add funds to your wallet.')
            return redirect('wallet_deposit')
        
        # Cast amounts to Decimal to ensure proper math operations
        milestone_amount = Decimal(str(milestone.amount))
        
        # Create a database transaction to ensure atomicity
        with transaction.atomic():
            # Move funds from balance to escrow
            wallet.balance -= milestone_amount
            wallet.escrow_balance += milestone_amount
            wallet.save()  # Save the wallet changes immediately
            
            # Create escrow transaction record
            transaction_record = Transaction.objects.create(
                wallet=wallet,
                project=project,
                milestone=milestone,
                amount=milestone_amount,
                transaction_type='escrow',
                payment_method='wallet',
                status='completed',
                description=f'Escrow for milestone: {milestone.title}'
            )
            
            # Update milestone status to funded
            milestone.status = 'funded'
            milestone.save()
            
            # Add project activity
            ProjectActivity.objects.create(
                project=project,
                user=request.user,
                activity_type='milestone_created',
                description=f'Milestone "{milestone.title}" has been funded with {milestone_amount}'
            )
            
            # Notify freelancer if assigned
            if project.assigned_freelancer:
                Notification.objects.create(
                    recipient=project.assigned_freelancer,
                    notification_type='milestone',
                    project=project,
                    message=f'Milestone "{milestone.title}" has been funded with {milestone_amount}',
                    is_read=False
                )
        
        messages.success(request, f'Successfully funded milestone: {milestone.title}')
        return redirect('project_milestones', project_id=project.id)
    
    context = {
        'project': project,
        'milestone': milestone,
        'wallet': wallet,
        'insufficient_funds': wallet.balance < milestone.amount
    }
    
    return render(request, 'wallet/fund_milestone.html', context)

@login_required
def leave_project_review(request, project_id):
    """Leave a review for a completed project"""
    project = get_object_or_404(Project, id=project_id)
    user_profile = request.user.userprofile
    
    # Check if user is client or freelancer
    if user_profile not in [project.client, project.assigned_freelancer]:
        messages.error(request, "Only project participants can leave reviews.")
        return redirect('project_detail', project_id=project_id)
    
    # Check if project is completed
    if project.status != 'completed':
        messages.error(request, "Can only review completed projects.")
        return redirect('project_detail', project_id=project_id)
    
    # Check if user has already reviewed
    if ProjectReview.objects.filter(project=project, reviewer=user_profile).exists():
        messages.error(request, "You have already reviewed this project.")
        return redirect('project_detail', project_id=project_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text')
        is_public = request.POST.get('is_public') == 'on'
        
        if rating and review_text:
            # Set the reviewed user based on who is leaving the review
            reviewed_user = project.assigned_freelancer if user_profile == project.client else project.client
            
            review = ProjectReview.objects.create(
                project=project,
                reviewer=user_profile,
                reviewed=reviewed_user,
                rating=rating,
                review_text=review_text,
                is_public=is_public
            )
            
            # Create notification for the reviewed user
            create_notification(
                recipient=review.reviewed,
                notification_type='review',
                message=f"New review received for project '{project.title}'",
                sender=user_profile,
                project=project
            )
            
            messages.success(request, "Review submitted successfully!")
            return redirect('project_detail', project_id=project_id)
        else:
            messages.error(request, "Please provide both rating and review text.")
    
    return render(request, 'projects/leave_review.html', {
        'project': project,
        'reviewer': user_profile
    })

@login_required
def project_reviews(request, project_id):
    """View all reviews for a project"""
    project = get_object_or_404(Project, id=project_id)
    reviews = ProjectReview.objects.filter(project=project, is_public=True)
    
    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Get rating distribution
    rating_distribution = reviews.values('rating').annotate(count=Count('id')).order_by('-rating')
    
    # Check if user can review
    can_review = False
    user_review = None
    if request.user.is_authenticated:
        user_profile = request.user.userprofile
        if project.status == 'completed' and user_profile in [project.client, project.assigned_freelancer]:
            user_review = ProjectReview.objects.filter(project=project, reviewer=user_profile).first()
            can_review = not user_review
    
    context = {
        'project': project,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'rating_distribution': rating_distribution,
        'total_reviews': reviews.count(),
        'can_review': can_review,
        'user_review': user_review
    }
    
    return render(request, 'projects/project_reviews.html', context)

@login_required
def edit_review(request, project_id, review_id):
    """Edit an existing review"""
    review = get_object_or_404(ProjectReview, id=review_id, project_id=project_id)
    
    # Check if user is the reviewer
    if request.user.userprofile != review.reviewer:
        messages.error(request, "You can only edit your own reviews.")
        return redirect('project_reviews', project_id=project_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text')
        is_public = request.POST.get('is_public') == 'on'
        
        if rating and review_text:
            review.rating = rating
            review.review_text = review_text
            review.is_public = is_public
            review.save()
            
            messages.success(request, "Review updated successfully!")
            return redirect('project_reviews', project_id=project_id)
        else:
            messages.error(request, "Please provide both rating and review text.")
    
    return render(request, 'projects/edit_review.html', {
        'project': review.project,
        'review': review
    })

@login_required
def delete_review(request, project_id, review_id):
    """Delete a review"""
    review = get_object_or_404(ProjectReview, id=review_id, project_id=project_id)
    
    # Check if user is the reviewer
    if request.user.userprofile != review.reviewer:
        messages.error(request, "You can only delete your own reviews.")
        return redirect('project_reviews', project_id=project_id)
    
    if request.method == 'POST' and request.POST.get('confirm_delete') == 'yes':
        review.delete()
        messages.success(request, "Review deleted successfully!")
        return redirect('project_reviews', project_id=project_id)
    
    return render(request, 'projects/confirm_delete_review.html', {
        'project': review.project,
        'review': review
    })
