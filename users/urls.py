# users/urls.py
from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CouncilMemberViewSet, FacultyViewSet, filter_users  # Ensure these are imported


router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'council-members', views.CouncilMemberViewSet)
router.register(r'faculty', views.FacultyViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Authentication & Registration
    path('register/', views.register_user, name='register'),
    path('register/verify/', views.verify_otp, name='verify-registration'),
    path('login/', views.login_user, name='login'),
    path('resend-otp/', views.resend_otp, name='resend-otp'),
    path('logout/', views.logout_user, name='logout'),
    path('request-password-reset/', views.request_password_reset, name='request-password-reset'),
    path('reset-password/', views.reset_password, name='reset-password'),
    
    # Profile Management
    path('profile/', views.user_profile, name='profile'),
    path('profile/update/', views.update_profile, name='update-profile'),
    path('profile/change-password/', views.change_password, name='change-password'),
    path('profile/upload-id-card/', views.upload_id_card, name='upload-id-card'),
    
    # User Management
    path('users/by-department/<str:department>/', views.users_by_department, name='users-by-department'),
    path('users/by-year/<str:year>/', views.users_by_year, name='users-by-year'),
    path('users/by-division/<str:division>/', views.users_by_division, name='users-by-division'),
    
    # Council Members
    path('council-members/', views.council_members_list, name='council-members'),
    path('promote-to-council/<int:user_id>/', views.promote_to_council, name='promote-to-council'),
    path('demote-from-council/<int:user_id>/', views.demote_from_council, name='demote-from-council'),
    path('council-members/active/', views.active_council_members, name='active-council-members'),
    path('council-members/expired/', views.expired_council_members, name='expired-council-members'),
    
    # Faculty
    path('faculty/', views.faculty_list, name='faculty-list'),
    path('faculty/by-department/<str:department>/', views.faculty_by_department, name='faculty-by-department'),
    path('faculty/by-subject/<str:subject>/', views.faculty_by_subject, name='faculty-by-subject'),
    
    # ID Card Management
    path('view-id-card/<int:user_id>/', views.view_id_card, name='view-id-card'),
    path('verify-id-card/<int:user_id>/', views.verify_id_card, name='verify-id-card'),
    
    # Statistics and Reports
    path('stats/users-summary/', views.users_summary, name='users-summary'),
    path('stats/department-distribution/', views.department_distribution, name='department-distribution'),
    path('stats/year-distribution/', views.year_distribution, name='year-distribution'),
    
    # Detailed User Information
    path('users/<int:user_id>/detail/', views.user_detail, name='user-detail'),
    path('users/<str:username>/detail/', views.user_detail_by_username, name='user-detail-by-username'),
    
    # Detailed Council Member Information
    path('council-members/<int:member_id>/detail/', views.council_member_detail, name='council-member-detail'),
    path('council-members/history/<int:user_id>/', views.council_member_history, name='council-member-history'),
    
    # Detailed Faculty Information
    path('faculty/<int:faculty_id>/detail/', views.faculty_detail, name='faculty-detail'),
    path('faculty/schedule/<int:faculty_id>/', views.faculty_schedule, name='faculty-schedule'),
    
    path('filter/', filter_users, name='filter-users'),
]

urlpatterns += router.urls