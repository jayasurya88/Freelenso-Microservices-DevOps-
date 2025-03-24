from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='view_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.view_freelancer_profile, name='view_freelancer_profile'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('projects/<int:project_id>/apply/', views.apply_to_project, name='apply_to_project'),
    path('projects/<int:project_id>/applications/', views.manage_applications, name='manage_applications'),
    path('projects/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('my-projects/', views.my_projects, name='my_projects'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('applications/<int:application_id>/withdraw/', views.withdraw_application, name='withdraw_application'),
    path('projects/<int:project_id>/workspace/', views.project_workspace, name='project_workspace'),
    path('projects/<int:project_id>/upload/', views.upload_project_file, name='upload_file'),
    path('projects/<int:project_id>/chat/', views.chat_room, name='chat_room'),
    path('projects/<int:project_id>/chat/send/', views.send_message, name='send_message'),
    path('projects/<int:project_id>/chat/messages/', views.get_messages, name='get_messages'),
    path('projects/<int:project_id>/chat/messages/<int:message_id>/read/', views.mark_message_read, name='mark_message_read'),
    path('messages/', views.message_list, name='message_list'),
    path('messages/cleanup/', views.cleanup_messages, name='cleanup_messages'),
    
    # Notification URLs
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # Milestone management
    path('projects/<int:project_id>/milestones/', views.project_milestones, name='project_milestones'),
    path('projects/<int:project_id>/milestones/create/', views.create_milestone, name='create_milestone'),
    path('projects/<int:project_id>/milestones/<int:milestone_id>/edit/', views.edit_milestone, name='edit_milestone'),
    path('projects/<int:project_id>/milestones/<int:milestone_id>/delete/', views.delete_milestone, name='delete_milestone'),
    path('projects/<int:project_id>/milestones/<int:milestone_id>/complete/', views.complete_milestone, name='complete_milestone'),
    path('projects/<int:project_id>/milestones/<int:milestone_id>/approve/', views.approve_milestone, name='approve_milestone'),
    path('projects/<int:project_id>/milestones/<int:milestone_id>/reject/', views.reject_milestone, name='reject_milestone'),
]
