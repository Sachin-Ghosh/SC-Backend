# users/urls.py
from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CouncilMemberViewSet, FacultyViewSet  # Ensure these are imported


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'council-members', CouncilMemberViewSet)
router.register(r'faculty', FacultyViewSet)


urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('register/verify/', views.verify_and_complete_registration, name='verify-registration'),
    path('login/', views.login_user, name='login'),
    path('profile/', views.user_profile, name='profile'),
    path('profile/update/', views.update_profile, name='update-profile'),
    path('council-members/', views.council_members_list, name='council-members'),
    path('faculty/', views.faculty_list, name='faculty-list'),
    path('promote-to-council/<int:user_id>/', views.promote_to_council, name='promote-to-council'),
    path('view-id-card/<int:user_id>/', views.view_id_card, name='view-id-card'),
]

urlpatterns += router.urls