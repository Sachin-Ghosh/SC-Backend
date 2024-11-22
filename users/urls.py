# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('register/verify/', views.verify_and_complete_registration, name='verify-registration'),
    path('login/', views.login_user, name='login'),
    path('profile/', views.user_profile, name='profile'),
    path('profile/update/', views.update_profile, name='update-profile'),
    path('council-members/', views.council_members_list, name='council-members'),
    path('faculty/', views.faculty_list, name='faculty-list'),
]