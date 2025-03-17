from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Project, ProjectApplication, ProjectMilestone, ProjectAttachment
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
import os

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
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.is_freelancer:
        return render(request, 'freelancer_dashboard.html', {'profile': user_profile})
    else:
        return render(request, 'client_dashboard.html', {'profile': user_profile})

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
    
    # Check if user has already applied
    has_applied = ProjectApplication.objects.filter(
        project=project,
        freelancer=user_profile
    ).exists()
    
    # Get application if exists
    application = None
    if has_applied:
        application = ProjectApplication.objects.get(
            project=project,
            freelancer=user_profile
        )
    
    context = {
        'project': project,
        'has_applied': has_applied,
        'application': application,
        'is_owner': project.client == user_profile,
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
    
    if not user_profile.is_freelancer:
        messages.error(request, 'Only freelancers can apply to projects')
        return redirect('project_detail', project_id=project_id)
    
    if project.status != 'open':
        messages.error(request, 'This project is no longer accepting applications')
        return redirect('project_detail', project_id=project_id)
    
    if ProjectApplication.objects.filter(project=project, freelancer=user_profile).exists():
        messages.error(request, 'You have already applied to this project')
        return redirect('project_detail', project_id=project_id)
    
    if request.method == 'POST':
        try:
            application = ProjectApplication(
                project=project,
                freelancer=user_profile,
                cover_letter=request.POST.get('cover_letter'),
                proposed_budget=request.POST.get('proposed_budget'),
                estimated_duration=request.POST.get('estimated_duration')
            )
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
    
    if project.client != user_profile:
        messages.error(request, 'You do not have permission to manage this project')
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
    
    applications = ProjectApplication.objects.filter(project=project)
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
