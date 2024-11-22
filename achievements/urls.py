from django.urls import path
from . import views

urlpatterns = [
    # Basic CRUD operations
    path('', views.achievement_list, name='achievement-list'),
    path('create/', views.create_achievement, name='create-achievement'),
    path('<slug:slug>/', views.achievement_detail, name='achievement-detail'),
    path('<slug:slug>/verify/', views.verify_achievement, name='verify-achievement'),
    
    # Additional endpoints (add these to views.py as well)
    path('my-achievements/', views.my_achievements, name='my-achievements'),
    path('pending-verification/', views.pending_verification, name='pending-verification'),
    path('<slug:slug>/update/', views.update_achievement, name='update-achievement'),
    path('<slug:slug>/delete/', views.delete_achievement, name='delete-achievement'),
]