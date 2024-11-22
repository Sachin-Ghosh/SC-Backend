# events/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Main Event URLs
    path('', views.event_list, name='event-list'),
    path('create/', views.create_event, name='create-event'),
    path('<slug:slug>/', views.event_detail, name='event-detail'),
    path('<slug:slug>/update/', views.update_event, name='update-event'),
    path('<slug:slug>/delete/', views.delete_event, name='delete-event'),
    
    # Sub-Event URLs
    path('<slug:event_slug>/sub-events/', views.sub_event_list, name='sub-event-list'),
    path('<slug:event_slug>/sub-events/create/', views.create_sub_event, name='create-sub-event'),
    path('<slug:event_slug>/sub-events/<slug:sub_event_slug>/', views.sub_event_detail, name='sub-event-detail'),
    path('<slug:event_slug>/sub-events/<slug:sub_event_slug>/update/', views.update_sub_event, name='update-sub-event'),
    path('<slug:event_slug>/sub-events/<slug:sub_event_slug>/delete/', views.delete_sub_event, name='delete-sub-event'),
    
    # Registration URLs
    path('register/<slug:sub_event_slug>/', views.register_event, name='register-event'),
    path('registrations/my/', views.my_registrations, name='my-registrations'),
    path('registrations/<int:registration_id>/cancel/', views.cancel_registration, name='cancel-registration'),
    
    # Score URLs
    path('scores/<slug:sub_event_slug>/', views.event_scores, name='event-scores'),
    path('scores/<slug:sub_event_slug>/add/', views.add_score, name='add-score'),
    path('scores/<slug:sub_event_slug>/update/<int:score_id>/', views.update_score, name='update-score'),
    
    # Department and Statistics URLs
    path('department-scores/', views.department_scores, name='department-scores'),
    path('statistics/', views.event_statistics, name='event-statistics'),
]