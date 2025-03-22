from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Project, ProjectApplication, ProjectMilestone, ProjectAttachment, ProjectFile, ProjectActivity, ChatRoom, ChatMessage, ChatParticipant
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
import os
from django.http import JsonResponse
import json
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.paginator import Paginator
from django.utils.text import slugify
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

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
    user_profile = UserProfile.objects.get(user=request.user)
    
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

@login_required
def profile_view(request):
    profile = UserProfile.objects.get(user=request.user)
    context = {
        'profile': profile,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'profile/view_profile.html', context)

@login_required
def edit_profile(request):
    profile = UserProfile.objects.get(user=request.user)
    
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
    
    context = {
        'project': project,
        'has_active_application': has_active_application,
        'application': application,
        'is_owner': project.client == user_profile,
        'active_applications_count': active_applications_count,
        'applications': applications,
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
def view_profile(request):
    profile = request.user.userprofile
    return render(request, 'profile/view_profile.html', {'profile': profile})

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
    
    context = {
        'freelancer': freelancer,
        'completed_projects': completed_projects,
        'active_applications': active_applications,
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
    
    # Get messages
    messages_list = ChatMessage.objects.filter(room=chat_room).order_by('created_at')
    
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
@require_POST
def send_message(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    user_profile = request.user.userprofile
    
    # Check if user has access to this project
    if user_profile != project.client and user_profile != project.assigned_freelancer:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get or create chat room
    chat_room, created = ChatRoom.objects.get_or_create(project=project)
    
    message_text = request.POST.get('message', '').strip()
    file = request.FILES.get('file')
    
    if not message_text and not file:
        return JsonResponse({'error': 'No message or file provided'}, status=400)
    
    # Save file if provided
    file_url = None
    if file:
        file_path = f'chat_files/{project_id}/{file.name}'
        file_url = default_storage.save(file_path, ContentFile(file.read()))
    
    # Create message
    message = ChatMessage.objects.create(
        room=chat_room,
        sender=user_profile,
        message=message_text,
        file=file_url
    )
    
    # Update last message timestamp
    chat_room.last_message_at = timezone.now()
    chat_room.save()
    
    return JsonResponse({
        'id': message.id,
        'message': message.message,
        'sender_id': message.sender.id,
        'sender_name': message.sender.user.username,
        'created_at': message.created_at.strftime('%b %d, %Y %H:%M'),
        'file_url': message.file.url if message.file else None
    })

@login_required
def get_messages(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    user_profile = request.user.userprofile
    
    # Check if user has access to this project
    if user_profile != project.client and user_profile != project.assigned_freelancer:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get chat room
    chat_room = get_object_or_404(ChatRoom, project=project)
    
    # Get messages
    messages_list = ChatMessage.objects.filter(room=chat_room).order_by('created_at')
    
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
