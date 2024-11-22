# grievances/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Grievance URLs
    path('', views.grievance_list, name='grievance-list'),
    path('create/', views.create_grievance, name='create-grievance'),
    path('<int:pk>/', views.grievance_detail, name='grievance-detail'),
    path('<int:pk>/update/', views.update_grievance, name='update-grievance'),
    path('<int:pk>/delete/', views.delete_grievance, name='delete-grievance'),
    
    # Grievance Status Management
    path('<int:pk>/assign/', views.assign_grievance, name='assign-grievance'),
    path('<int:pk>/resolve/', views.resolve_grievance, name='resolve-grievance'),
    path('<int:pk>/reject/', views.reject_grievance, name='reject-grievance'),
    
    # Evidence Management
    path('<int:pk>/evidence/', views.add_evidence, name='add-evidence'),
    path('<int:pk>/evidence/<int:evidence_id>/', views.remove_evidence, name='remove-evidence'),
    
    # Media File Management
    path('media/upload/', views.upload_media, name='upload-media'),
    path('media/<int:pk>/', views.media_detail, name='media-detail'),
    path('media/<int:pk>/delete/', views.delete_media, name='delete-media'),
    
    # Filtering and Statistics
    path('my-grievances/', views.my_grievances, name='my-grievances'),
    path('assigned-grievances/', views.assigned_grievances, name='assigned-grievances'),
    path('statistics/', views.grievance_statistics, name='grievance-statistics'),
]