# events/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'organizations', views.OrganizationViewSet)
router.register(r'events', views.EventViewSet)
router.register(r'sub-events', views.SubEventViewSet)
router.register(r'registrations', views.EventRegistrationViewSet, basename='event-registration')
router.register(r'draws', views.EventDrawViewSet)
router.register(r'scores', views.EventScoreViewSet, basename='event-score')
# router.register(r'faculty-judges', views.SubEventFacultyViewSet, basename='sub-event-faculty')

urlpatterns = [
    path('', include(router.urls)),
    
    # Event Statistics and Draws
    path('events/<slug:event_slug>/statistics/', views.event_statistics, name='event-statistics'),
    path('sub-events/<slug:sub_event_slug>/generate-draws/', views.generate_draws, name='generate-draws'),
    
    # Event Management
    path('events/<slug:slug>/add-organizers/', views.EventViewSet.as_view({'post': 'add_organizers'}), name='add-organizers'),
    path('events/<slug:slug>/remove-organizers/', views.EventViewSet.as_view({'post': 'remove_organizers'}), name='remove-organizers'),
    path('events/<slug:slug>/update-status/', views.EventViewSet.as_view({'post': 'update_status'}), name='update-event-status'),
    
    # Sub-Event Management
    path('sub-events/<slug:slug>/add-images/', views.SubEventViewSet.as_view({'post': 'add_images'}), name='add-sub-event-images'),
    path('sub-events/<slug:slug>/update-stage/', views.SubEventViewSet.as_view({'post': 'update_stage'}), name='update-sub-event-stage'),
    path('sub-events/<slug:slug>/participants/', views.SubEventViewSet.as_view({'get': 'participants'}), name='sub-event-participants'),
    
    # Registration Management
    path('registrations/<int:pk>/approve/', views.EventRegistrationViewSet.as_view({'post': 'approve'}), name='approve-registration'),
    path('registrations/<int:pk>/reject/', views.EventRegistrationViewSet.as_view({'post': 'reject'}), name='reject-registration'),
    path('registrations/<int:pk>/submit-files/', views.EventRegistrationViewSet.as_view({'post': 'submit_files'}), name='submit-files'),
    path('registrations/my/', views.EventRegistrationViewSet.as_view({'get': 'my_registrations'}), name='my-registrations'),
    
    # Scoring and Results
    path('scores/add/', views.EventScoreViewSet.as_view({'post': 'create'}), name='add-score'),
    path('scores/<int:pk>/update/', views.EventScoreViewSet.as_view({'put': 'update'}), name='update-score'),
    path('sub-events/<slug:slug>/leaderboard/', views.SubEventViewSet.as_view({'get': 'leaderboard'}), name='sub-event-leaderboard'),
    path('events/<slug:slug>/department-scores/', views.EventViewSet.as_view({'get': 'department_scores'}), name='department-scores'),
    path('sub-events/<slug:slug>/generate-heats/', 
         views.SubEventViewSet.as_view({'post': 'generate_heats'}),
         name='generate-heats'),
    path('sub-events/<slug:slug>/record-heat-results/', 
         views.SubEventViewSet.as_view({'post': 'record_heat_results'}),
         name='record-heat-results'),
    path('sub-events/<slug:slug>/round-summary/', 
         views.SubEventViewSet.as_view({'get': 'round_summary'}),
         name='round-summary'),
    path('events/<slug:slug>/all-participants/', 
         views.EventViewSet.as_view({'get': 'all_participants'}),
         name='event-all-participants'),
    path('events/<slug:slug>/department-statistics/', 
         views.EventViewSet.as_view({'get': 'department_statistics'}),
         name='event-department-statistics'),
    path('sub-events/<slug:slug>/round-participants/', 
         views.SubEventViewSet.as_view({'get': 'round_participants'}),
         name='round-participants'),
    path('registrations/available-team-members/', 
         views.EventRegistrationViewSet.as_view({'get': 'available_team_members'}),
         name='available-team-members'),
]