from django.urls import path
from . import views
from . import admin_views

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
    path('notifications/mark-all-read/', views.mark_all_read, name='mark_all_read'),
    
    # Milestone management
    path('projects/<int:project_id>/milestones/', views.project_milestones, name='project_milestones'),
    path('projects/<int:project_id>/milestones/create/', views.create_milestone, name='create_milestone'),
    path('projects/<int:project_id>/milestones/<int:milestone_id>/edit/', views.edit_milestone, name='edit_milestone'),
    path('projects/<int:project_id>/milestones/<int:milestone_id>/delete/', views.delete_milestone, name='delete_milestone'),
    path('projects/<int:project_id>/milestones/<int:milestone_id>/complete/', views.complete_milestone, name='complete_milestone'),
    path('projects/<int:project_id>/milestones/<int:milestone_id>/approve/', views.approve_milestone, name='approve_milestone'),
    path('projects/<int:project_id>/milestones/<int:milestone_id>/reject/', views.reject_milestone, name='reject_milestone'),
    
    # Wallet URLs
    path('wallet/', views.wallet_dashboard, name='wallet_dashboard'),
    path('wallet/deposit/', views.wallet_deposit, name='wallet_deposit'),
    # path('wallet/deposit/confirm/', views.wallet_deposit_confirm, name='wallet_deposit_confirm'), # Comment out or remove if confirm page is no longer needed
    path('wallet/razorpay/create-order/', views.create_razorpay_order, name='create_razorpay_order'), # New Razorpay order URL
    path('wallet/razorpay/verify-payment/', views.verify_razorpay_payment, name='verify_razorpay_payment'), # New Razorpay verification URL
    path('wallet/withdraw/', views.wallet_withdraw, name='wallet_withdraw'),
    path('wallet/transactions/', views.wallet_transactions, name='wallet_transactions'),
    path('wallet/escrow/', views.wallet_escrow_records, name='wallet_escrow_records'),
    path('wallet/payment-methods/', views.payment_methods, name='payment_methods'),
    path('wallet/payment-methods/add/', views.add_payment_method, name='add_payment_method'),
    path('wallet/payment-methods/<int:method_id>/delete/', views.delete_payment_method, name='delete_payment_method'),
    path('wallet/payment-methods/<int:method_id>/set-default/', views.set_default_payment_method, name='set_default_payment_method'),
    
    # Escrow and project payments
    path('projects/<int:project_id>/fund-milestone/<int:milestone_id>/', views.fund_milestone, name='fund_milestone'),
    
    # Custom Admin Dashboard URLs
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/users/', admin_views.admin_users, name='admin_users'),
    path('admin-dashboard/users/export/', admin_views.admin_export_users, name='admin_export_users'),
    path('admin-dashboard/users/<int:user_id>/activate/', admin_views.admin_activate_user, name='admin_activate_user'),
    path('admin-dashboard/users/<int:user_id>/deactivate/', admin_views.admin_deactivate_user, name='admin_deactivate_user'),
    path('admin-dashboard/projects/', admin_views.admin_projects, name='admin_projects'),
    path('admin-dashboard/projects/<int:project_id>/cancel/', admin_views.admin_cancel_project, name='admin_cancel_project'),
    path('admin-dashboard/transactions/', admin_views.admin_transactions, name='admin_transactions'),
    path('admin-dashboard/withdrawals/', admin_views.admin_withdrawals, name='admin_withdrawals'),
    path('admin-dashboard/withdrawals/<int:withdrawal_id>/process/', admin_views.admin_process_withdrawal, name='admin_process_withdrawal'),
    path('admin-dashboard/stats/', admin_views.admin_system_stats, name='admin_system_stats'),
    
    # Review URLs
    path('projects/<int:project_id>/review/', views.leave_project_review, name='leave_review'),
    path('projects/<int:project_id>/reviews/', views.project_reviews, name='project_reviews'),
    path('projects/<int:project_id>/reviews/<int:review_id>/edit/', views.edit_review, name='edit_review'),
    path('projects/<int:project_id>/reviews/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    
    # Milestone delay handling
    path('projects/milestone/<int:milestone_id>/handle-delay/', views.handle_milestone_delay, name='handle_milestone_delay'),
    path('projects/milestone/<int:milestone_id>/extend-deadline/', views.extend_milestone_deadline, name='extend_milestone_deadline'),
    path('projects/milestone/<int:milestone_id>/check-delay/', views.check_milestone_delay, name='check_milestone_delay'),
    
    # Admin-only routes
    path('check-for-delays/', views.check_for_delays, name='check_for_delays'),
]
