from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db import models 
from django.shortcuts import get_object_or_404
from .models import Event, SubEvent, EventRegistration, EventScore, EventDraw , Organization , SubEventImage, EventHeat , SubmissionFile , User, SubEventFaculty, DepartmentScore, HeatParticipant, EventCriteria, DepartmentTotal
from .serializers import EventSerializer, SubEventSerializer, EventRegistrationSerializer, EventScoreSerializer, EventDrawSerializer , OrganizationSerializer , SubEventImageSerializer, EventHeatSerializer, SubEventFacultySerializer, HeatParticipantSerializer, EventScoreSerializer , UserSerializer, EventCriteriaSerializer
from rest_framework import viewsets, status     
from django.db.models import Q, Count, Avg, Sum, IntegerField, Min , Max
from decimal import Decimal
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.decorators import action
from rest_framework.routers import DefaultRouter
from rest_framework.views import APIView
import random
from django.db.models import Prefetch
from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.exceptions import PermissionDenied
from django.db.models.functions import Coalesce
from rest_framework.exceptions import ValidationError
from django.http import HttpResponse
import csv
from datetime import datetime
from django.db.models import Max
from collections import OrderedDict

# Get the custom User model
User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def event_list(request):
    events = Event.objects.filter(is_active=True)
    serializer = EventSerializer(events, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_event(request):
    if not request.user.user_type in ['ADMIN', 'COUNCIL']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = EventSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def event_detail(request, slug):
    event = get_object_or_404(Event, slug=slug)
    serializer = EventSerializer(event)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_event(request, slug):
    if not request.user.user_type in ['ADMIN', 'COUNCIL']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    event = get_object_or_404(Event, slug=slug)
    serializer = EventSerializer(event, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_event(request, slug):
    event = get_object_or_404(Event, slug=slug)
    event.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

# Sub-Event Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sub_event_list(request, event_slug):
    sub_events = SubEvent.objects.filter(event__slug=event_slug)
    serializer = SubEventSerializer(sub_events, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_sub_event(request, event_slug):
    if not request.user.user_type in ['ADMIN', 'COUNCIL']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    event = get_object_or_404(Event, slug=event_slug)
    serializer = SubEventSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(event=event)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_event(request, sub_event_slug):
    sub_event = get_object_or_404(SubEvent, slug=sub_event_slug)
    
    # Check if already registered
    if EventRegistration.objects.filter(sub_event=sub_event, participant=request.user).exists():
        return Response({'error': 'Already registered'}, status=status.HTTP_400_BAD_REQUEST)
    
    registration_data = {
        'sub_event': sub_event.id,
        'participant': request.user.id,
        'department': request.user.department,
        **request.data
    }
    
    serializer = EventRegistrationSerializer(data=registration_data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_registrations(request):
    registrations = EventRegistration.objects.filter(participant=request.user)
    serializer = EventRegistrationSerializer(registrations, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_score(request, sub_event_slug):
    if not request.user.user_type in ['ADMIN', 'COUNCIL', 'FACULTY']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    sub_event = get_object_or_404(SubEvent, slug=sub_event_slug)
    score_data = {
        'sub_event': sub_event.id,
        'judge': request.user.id,
        'updated_by': request.user.id,
        **request.data
    }
    
    serializer = EventScoreSerializer(data=score_data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def department_scores(request):
    department = request.query_params.get('department')
    scores = EventScore.objects.filter(department=department)
    serializer = EventScoreSerializer(scores, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def event_statistics(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    sub_events = event.sub_events.all()
    
    statistics = {
        'total_registrations': EventRegistration.objects.filter(sub_event__event=event).count(),
        'sub_events': [],
        'department_wise': {},
        'year_wise': {}
    }
    
    for sub_event in sub_events:
        registrations = EventRegistration.objects.filter(sub_event=sub_event)
        statistics['sub_events'].append({
            'name': sub_event.name,
            'total_participants': registrations.count(),
            'stage_wise': registrations.values('current_stage').annotate(count=Count('id')),
            'average_score': EventScore.objects.filter(sub_event=sub_event).aggregate(Avg('total_score'))
        })
        
        # Department and year wise statistics
        dept_stats = registrations.values('department').annotate(count=Count('id'))
        year_stats = registrations.values('year').annotate(count=Count('id'))
        
        for stat in dept_stats:
            dept = stat['department']
            if dept not in statistics['department_wise']:
                statistics['department_wise'][dept] = 0
            statistics['department_wise'][dept] += stat['count']
        
        for stat in year_stats:
            year = stat['year']
            if year not in statistics['year_wise']:
                statistics['year_wise'][year] = 0
            statistics['year_wise'][year] += stat['count']
    
    return Response(statistics)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_sub_event(request, event_slug, sub_event_slug):
    if not request.user.user_type in ['ADMIN', 'COUNCIL']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    sub_event = get_object_or_404(SubEvent, event__slug=event_slug, slug=sub_event_slug)
    serializer = SubEventSerializer(sub_event, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_sub_event(request, event_slug, sub_event_slug):
    if not request.user.user_type in ['ADMIN', 'COUNCIL']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    sub_event = get_object_or_404(SubEvent, event__slug=event_slug, slug=sub_event_slug)
    sub_event.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_registration(request, registration_id):
    registration = get_object_or_404(EventRegistration, id=registration_id, participant=request.user)
    
    # Check if the event hasn't started yet
    if registration.sub_event.schedule <= timezone.now():
        return Response({
            'error': 'Cannot cancel registration after event has started'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    registration.status = 'CANCELLED'
    registration.save()
    return Response({
        'message': 'Registration cancelled successfully'
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def event_scores(request, sub_event_slug):
    sub_event = get_object_or_404(SubEvent, slug=sub_event_slug)
    scores = EventScore.objects.filter(sub_event=sub_event)
    
    # Only allow viewing scores if user is admin, council, faculty, or a participant
    if not (request.user.user_type in ['ADMIN', 'COUNCIL', 'FACULTY'] or 
            EventRegistration.objects.filter(sub_event=sub_event, participant=request.user).exists()):
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = EventScoreSerializer(scores, many=True)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_score(request, sub_event_slug, score_id):
    if not request.user.user_type in ['ADMIN', 'COUNCIL', 'FACULTY']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    score = get_object_or_404(EventScore, id=score_id, sub_event__slug=sub_event_slug)
    
    # Only allow the original judge or admin to update scores
    if not (request.user.is_staff or score.judge == request.user):
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = EventScoreSerializer(score, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save(updated_by=request.user)
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Organization ViewSet
class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

# Event ViewSet
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_organizers(self, request, slug=None):
        event = self.get_object()
        role = request.data.get('role')
        user_ids = request.data.get('user_ids', [])
        
        if role not in ['chairpersons', 'vice_chairpersons', 'event_heads']:
            return Response(
                {'error': 'Invalid role specified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        getattr(event, role).set(user_ids)
        return Response({'message': f'{role} updated successfully'})

    @action(detail=True, methods=['get'])
    def all_participants(self, request, slug=None):
        """Get all participants for an event across all sub-events"""
        event = self.get_object()
        participants = EventRegistration.objects.filter(
            sub_event__event=event
        ).select_related(
            'team_leader', 'sub_event'
        ).prefetch_related('team_members')

        # Filter options
        department = request.query_params.get('department')
        year = request.query_params.get('year')
        division = request.query_params.get('division')

        if department:
            participants = participants.filter(department=department)
        if year:
            participants = participants.filter(year=year)
        if division:
            participants = participants.filter(division=division)

        # Group by sub-event
        sub_event_participants = {}
        for registration in participants:
            if registration.sub_event.name not in sub_event_participants:
                sub_event_participants[registration.sub_event.name] = []
            sub_event_participants[registration.sub_event.name].append({
                'registration_id': registration.id,
                'team_leader': {
                    'id': registration.team_leader.id,
                    'name': f"{registration.team_leader.first_name} {registration.team_leader.last_name}",
                    'email': registration.team_leader.email,
                },
                'team_members': [{
                    'id': member.id,
                    'name': f"{member.first_name} {member.last_name}",
                    'email': member.email,
                } for member in registration.team_members.all()],
                'department': registration.department,
                'year': registration.year,
                'division': registration.division,
                'status': registration.status
            })

        return Response(sub_event_participants)

    @action(detail=True, methods=['get'])
    def department_statistics(self, request, slug=None):
        """Get detailed statistics by department"""
        event = self.get_object()
        stats = EventRegistration.objects.filter(
            sub_event__event=event
        ).values(
            'department', 'year', 'division'
        ).annotate(
            total_participants=Count('id'),
            total_teams=Count('team_name', distinct=True),
            average_score=Avg('scores__total_score'),
            total_score=Sum('scores__total_score'),
            qualified_participants=Count(
                'id',
                filter=Q(scores__qualified_for_next=True)
            )
        ).order_by('department', 'year', 'division')

        return Response(stats)

    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Get event dashboard statistics"""
        event = self.get_object()
        sub_events = SubEvent.objects.filter(event=event)
        
        return Response({
            'total_sub_events': sub_events.count(),
            'total_registrations': EventRegistration.objects.filter(
                sub_event__event=event).count(),
            'total_participants': EventRegistration.objects.filter(
                sub_event__event=event).values('team_members').distinct().count(),
            'upcoming_sub_events': sub_events.filter(
                schedule__gt=timezone.now()).count(),
            'completed_sub_events': sub_events.filter(
                schedule__lt=timezone.now()).count(),
            'total_faculty': SubEventFaculty.objects.filter(
                sub_event__event=event).values('faculty').distinct().count(),
        })

    @action(detail=True, methods=['get'])
    def get_all_faculty(self, request, pk=None):
        """Get all faculty members across all sub-events of this event"""
        event = self.get_object()
        faculty = SubEventFaculty.objects.filter(sub_event__event=event)
        
        # Filters
        department = request.query_params.get('department')
        is_active = request.query_params.get('is_active')
        search = request.query_params.get('search')
        
        if department:
            faculty = faculty.filter(faculty__department=department)
        if is_active is not None:
            faculty = faculty.filter(is_active=is_active)
        if search:
            faculty = faculty.filter(
                Q(faculty__first_name__icontains=search) |
                Q(faculty__last_name__icontains=search) |
                Q(faculty__email__icontains=search)
            )
        
        return Response(SubEventFacultySerializer(faculty, many=True).data)

    @action(detail=True, methods=['get'])
    def get_registration_stats(self, request, pk=None):
        """Get detailed registration statistics"""
        event = self.get_object()
        registrations = EventRegistration.objects.filter(sub_event__event=event)
        
        stats = {
            'total_registrations': registrations.count(),
            'by_status': dict(registrations.values('status')
                            .annotate(count=Count('id'))
                            .values_list('status', 'count')),
            'by_department': dict(registrations.values('department')
                                .annotate(count=Count('id'))
                                .values_list('department', 'count')),
            'by_year': dict(registrations.values('year')
                          .annotate(count=Count('id'))
                          .values_list('year', 'count')),
            'by_division': dict(registrations.values('division')
                              .annotate(count=Count('id'))
                              .values_list('division', 'count')),
        }
        return Response(stats)

    @action(detail=True, methods=['get'])
    def get_timeline(self, request, pk=None):
        """Get event timeline with sub-events"""
        event = self.get_object()
        sub_events = SubEvent.objects.filter(event=event).order_by('schedule')
        
        timeline = []
        for sub in sub_events:
            timeline.append({
                'id': sub.id,
                'name': sub.name,
                'schedule': sub.schedule,
                'venue': sub.venue,
                'current_stage': sub.current_stage,
                'registration_count': sub.event_registrations.count(),
                'faculty_count': sub.subeventfaculty_set.filter(is_active=True).count()
            })
        
        return Response(timeline)
    
    @action(detail=True, methods=['get'])
    def sub_events_summary(self, request, pk=None):
        """Get summary of all sub-events"""
        event = self.get_object()
        sub_events = SubEvent.objects.filter(event=event)
        
        return Response([{
            'id': sub.id,
            'name': sub.name,
            'registrations_count': sub.event_registrations.count(),
            'schedule': sub.schedule,
            'venue': sub.venue,
            'status': sub.current_stage,
        } for sub in sub_events])

# SubEvent ViewSet
class SubEventViewSet(viewsets.ModelViewSet):
    queryset = SubEvent.objects.all()
    serializer_class = SubEventSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        queryset = SubEvent.objects.all()
        
        if user.user_type == 'STUDENT_COUNCIL':
            return queryset
        
        # Get filter parameters
        category = self.request.query_params.get('category', None)
        event_id = self.request.query_params.get('event', None)
        participation_type = self.request.query_params.get('participation_type', None)
        current_stage = self.request.query_params.get('current_stage', None)
        gender = self.request.query_params.get('gender', None)
        
        # Apply filters if parameters are provided
        if category:
            queryset = queryset.filter(category=category)
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        if participation_type:
            queryset = queryset.filter(participation_type=participation_type)
        if current_stage:
            queryset = queryset.filter(current_stage=current_stage)
        if gender:
            if gender.upper() in ['MALE', 'FEMALE']:
                queryset = queryset.filter(
                    models.Q(gender_participation=gender.upper()) | 
                    models.Q(gender_participation='ALL')
                )
         # Filter based on user role
        # if user.user_type == 'COUNCIL':
            # Get sub-events where user is sub_head
            # queryset = queryset.filter(sub_heads=user)
        # if user.user_type == 'FACULTY':
        #     # Get sub-events where faculty is judge
        #     queryset = queryset.filter(faculty_judges=user)
            
        # Apply additional filters
        event_type = self.request.query_params.get('event_type', None)
        status = self.request.query_params.get('status', None)
        department = self.request.query_params.get('department', None)
        
        if event_type:
            queryset = queryset.filter(category=event_type)  # Changed from event_type to category
        if status:
            queryset = queryset.filter(current_stage=status)  # Changed from status to current_stage
        if department:
            queryset = queryset.filter(allow_mixed_department=False)  # Adjust based on your requirements
            
            
    
        return queryset.select_related('event').prefetch_related(
            'sub_heads',
            'images'
        )
        # return queryset.distinct()

    @action(detail=False, methods=['get'])
    def my_events(self, request):
        """Get events based on user's role and involvement"""
        user = request.user
        events = []
        
        if user.user_type == 'COUNCIL':
            # Get events where user is sub_head
            events = self.get_queryset().filter(sub_heads=user)
        elif user.user_type == 'FACULTY':
            # Get events where faculty is judge
            events = self.get_queryset().filter(faculty_judges=user)
        
        serializer = self.get_serializer(events, many=True)
        return Response({
            'count': len(events),
            'results': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Get sub-event details by ID with optional filters"""
        try:
            sub_event = self.get_object()
            
            # Get query parameters for filtering
            stage = request.query_params.get('stage')
            status_filter = request.query_params.get('status')
            registration_open = request.query_params.get('registration_open')
            has_results = request.query_params.get('has_results')
            
            # Get related data with filters
            registrations = sub_event.eventregistration_set.all()
            heats = sub_event.eventheat_set.all()
            scores = sub_event.eventscore_set.all()
            
            # Apply filters
            if stage:
                registrations = registrations.filter(current_stage=stage)
                heats = heats.filter(stage=stage)
            
            if status_filter:
                registrations = registrations.filter(status=status_filter)
                heats = heats.filter(status=status_filter)
            
            if registration_open is not None:
                registration_open = registration_open.lower() == 'true'
                if not registration_open:
                    registrations = registrations.none()
            
            # Get statistics
            stats = {
                'total_registrations': registrations.count(),
                'total_participants': registrations.aggregate(
                    total=Count('team_members') + Count('team_leader', distinct=True)
                )['total'],
                'total_heats': heats.count(),
                'total_scores': scores.count(),
                'registration_status': {
                    'PENDING': registrations.filter(status='PENDING').count(),
                    'APPROVED': registrations.filter(status='APPROVED').count(),
                    'REJECTED': registrations.filter(status='REJECTED').count(),
                },
                'stage_counts': {
                    stage: registrations.filter(current_stage=stage).count()
                } if sub_event.event else {}
            }
            
            # Serialize sub-event data
            serializer = self.get_serializer(sub_event)
            data = serializer.data
            
            # Add additional data
            data.update({
                'statistics': stats,
                'registrations': EventRegistrationSerializer(
                    registrations.select_related('team_leader')
                    .prefetch_related('team_members')[:10],  # Limit to 10 recent
                    many=True
                ).data,
                'recent_heats': EventHeatSerializer(
                    heats.order_by('-id')[:5],  # Order by id instead of created_at
                    many=True
                ).data,
                'recent_scores': EventScoreSerializer(
                    scores.order_by('-id')[:5],  # Order by id instead of updated_at
                    many=True
                ).data
            })
            
            return Response(data)
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    @action(detail=False, methods=['GET'])
    def filters(self, request):
        """Return all possible filter values"""
        return Response({
            'categories': dict(SubEvent.EVENT_CATEGORIES),
            'participation_types': dict(SubEvent.PARTICIPATION_TYPES),
            'stages': dict(SubEvent.EVENT_STAGES),
            'gender_participation': dict(SubEvent.GENDER_PARTICIPATION)
        })

    @action(detail=True, methods=['POST'])
    def add_images(self, request, slug=None):
        try:
            sub_event = self.get_object()
            images_data = request.FILES.getlist('images')
            captions = request.POST.getlist('captions', [''] * len(images_data))  # Default empty captions if not provided
            
            if not images_data:
                return Response({
                    'error': 'No images provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            created_images = []
            for image, caption in zip(images_data, captions):
                # Validate image file
                if not image.content_type.startswith('image/'):
                    return Response({
                        'error': f'File {image.name} is not an image'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    sub_event_image = SubEventImage.objects.create(
                        sub_event=sub_event,  # Add direct reference to sub_event
                        image=image,
                        caption=caption
                    )
                    created_images.append(sub_event_image)
                except Exception as e:
                    return Response({
                        'error': f'Failed to save image {image.name}: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # No need to use add() since we're already setting sub_event in create()
            return Response({
                'message': 'Images added successfully',
                'images': [{
                    'id': img.id,
                    'url': request.build_absolute_uri(img.image.url),
                    'caption': img.caption
                } for img in created_images]
            })
            
        except Exception as e:
            return Response({
                'error': f'Error adding images: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    @action(detail=True, methods=['get'])
    def get_faculty(self, request, pk=None):
        """Get all faculty members for this sub-event with filters"""
        sub_event = self.get_object()
        faculty = SubEventFaculty.objects.filter(sub_event=sub_event)
        
        # Apply filters
        is_active = request.query_params.get('is_active')
        department = request.query_params.get('department')
        search = request.query_params.get('search')
        
        if is_active is not None:
            faculty = faculty.filter(is_active=is_active)
        if department:
            faculty = faculty.filter(faculty__department=department)
        if search:
            faculty = faculty.filter(
                Q(faculty__first_name__icontains=search) |
                Q(faculty__last_name__icontains=search) |
                Q(faculty__email__icontains=search)
            )
        
        return Response(SubEventFacultySerializer(faculty, many=True).data)

    @action(detail=True, methods=['post'])
    def remove_faculty(self, request, pk=None):
        """Remove faculty from sub-event"""
        sub_event = self.get_object()
        faculty_ids = request.data.get('faculty_ids', [])
        
        if not faculty_ids:
            return Response({'error': 'faculty_ids required'}, status=400)
            
        SubEventFaculty.objects.filter(
            sub_event=sub_event,
            faculty_id__in=faculty_ids
        ).delete()
        
        return Response({'message': 'Faculty members removed successfully'})

    @action(detail=True, methods=['get'])
    def get_participants_by_department(self, request, pk=None):
        """Get participants grouped by department"""
        sub_event = self.get_object()
        participants = EventRegistration.objects.filter(sub_event=sub_event)
        
        department_data = {}
        for reg in participants:
            if reg.department not in department_data:
                department_data[reg.department] = {
                    'total': 0,
                    'approved': 0,
                    'pending': 0,
                    'rejected': 0
                }
            department_data[reg.department]['total'] += 1
            department_data[reg.department][reg.status.lower()] += 1
        
        return Response(department_data)

    @action(detail=True, methods=['get'])
    def get_participants_by_year(self, request, pk=None):
        """Get participants grouped by year"""
        sub_event = self.get_object()
        return Response(
            EventRegistration.objects.filter(sub_event=sub_event)
            .values('year')
            .annotate(count=Count('id'))
            .order_by('year')
        )

    @action(detail=True, methods=['get'])
    def get_scores_by_criteria(self, request, pk=None):
        """Get detailed scores breakdown by criteria"""
        sub_event = self.get_object()
        scores = EventScore.objects.filter(sub_event=sub_event)
        
        department = request.query_params.get('department')
        year = request.query_params.get('year')
        division = request.query_params.get('division')
        
        if department:
            scores = scores.filter(event_registration__department=department)
        if year:
            scores = scores.filter(event_registration__year=year)
        if division:
            scores = scores.filter(event_registration__division=division)
            
        return Response(EventScoreSerializer(scores, many=True).data)
    
    @action(detail=True, methods=['post'])
    def update_stage(self, request, slug=None):
        sub_event = self.get_object()
        new_stage = request.data.get('stage')
        
        if new_stage not in dict(SubEvent.EVENT_STAGES).keys():
            return Response(
                {'error': 'Invalid stage'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sub_event.current_stage = new_stage
        sub_event.save()
        
        # Update all active registrations to the new stage
        EventRegistration.objects.filter(
            sub_event=sub_event,
            status='APPROVED'
        ).update(current_stage=new_stage)
        
        return Response({'message': 'Stage updated successfully'})

    # @action(detail=True, methods=['post'])
    # def generate_heats(self, request, slug=None):
    #     """Generate heats for the next round"""
    #     sub_event = self.get_object()
    #     round_number = request.data.get('round_number', sub_event.current_round)
        
    #     # Get qualified participants for this round
    #     if round_number == 1:
    #         participants = EventRegistration.objects.filter(
    #             sub_event=sub_event,
    #             status='APPROVED'
    #         )
    #     else:
    #         # Get participants who qualified from previous round
    #         participants = EventRegistration.objects.filter(
    #             sub_event=sub_event,
    #             scores__round_number=round_number-1,
    #             scores__qualified_for_next=True
    #         ).distinct()
        
    #     # Shuffle participants
    #     participants = list(participants)
    #     random.shuffle(participants)
        
    #     # Create heats
    #     heats_needed = (len(participants) + sub_event.participants_per_group - 1) // sub_event.participants_per_group
        
    #     heats = []
    #     for heat_number in range(1, heats_needed + 1):
    #         heat = EventHeat.objects.create(
    #             sub_event=sub_event,
    #             round_number=round_number,
    #             heat_number=heat_number
    #         )
            
    #         # Assign participants to this heat
    #         start_idx = (heat_number - 1) * sub_event.participants_per_group
    #         end_idx = min(start_idx + sub_event.participants_per_group, len(participants))
    #         heat_participants = participants[start_idx:end_idx]
    #         heat.participants.set(heat_participants)
    #         heats.append(heat)
        
    #     serializer = EventHeatSerializer(heats, many=True)
    #     return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def record_heat_results(self, request, slug=None):
        """Record results for a heat"""
        heat_id = request.data.get('heat_id')
        results = request.data.get('results', [])  # List of participant results
        
        heat = get_object_or_404(EventHeat, id=heat_id)
        sub_event = heat.sub_event
        
        # Validate that all participants are in the heat
        participant_ids = set(result['participant_id'] for result in results)
        heat_participant_ids = set(heat.participants.values_list('id', flat=True))
        if not participant_ids.issubset(heat_participant_ids):
            return Response({'error': 'Invalid participant IDs'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Record scores and determine qualifiers
        for position, result in enumerate(results, 1):
            participant_id = result['participant_id']
            time_taken = result.get('time_taken')
            
            # Determine if participant qualifies for next round
            qualified = position <= sub_event.qualifiers_per_group
            
            EventScore.objects.create(
                sub_event=sub_event,
                event_registration_id=participant_id,
                heat=heat,
                round_number=heat.round_number,
                position=position,
                time_taken=time_taken,
                qualified_for_next=qualified,
                judge=request.user,
                total_score=result.get('score', 0)
            )
        
        heat.status = 'COMPLETED'
        heat.completed_time = timezone.now()
        heat.save()
        
        return Response({'message': 'Heat results recorded successfully'})

    @action(detail=True, methods=['get'])
    def round_summary(self, request, slug=None):
        """Get summary of a specific round"""
        sub_event = self.get_object()
        round_number = request.query_params.get('round', sub_event.current_round)
        
        heats = EventHeat.objects.filter(
            sub_event=sub_event,
            round_number=round_number
        ).prefetch_related('participants')
        
        qualified_participants = EventRegistration.objects.filter(
            sub_event=sub_event,
            scores__round_number=round_number,
            scores__qualified_for_next=True
        ).distinct()
        
        return Response({
            'round_number': round_number,
            'total_heats': heats.count(),
            'completed_heats': heats.filter(status='COMPLETED').count(),
            'qualified_participants': qualified_participants.count(),
            'heats': EventHeatSerializer(heats, many=True).data
        })
    @action(detail=True, methods=['post'], url_path='add-faculty')
    def add_faculty(self, request, pk=None):
        """Add faculty members to a sub-event"""
        try:
            sub_event = self.get_object()
            
            # Check if user has permission
            if not request.user.user_type in ['ADMIN', 'COUNCIL']:
                return Response({
                    'error': 'Only admin and council members can add faculty'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get faculty emails from request
            faculty_emails = request.data.get('faculty_emails', [])
            if not faculty_emails:
                return Response({
                    'error': 'faculty_emails is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not isinstance(faculty_emails, list):
                faculty_emails = [faculty_emails]
            
            results = {
                'success': [],
                'failed': []
            }
            
            for email in faculty_emails:
                try:
                    # Get faculty user
                    faculty = User.objects.get(email=email, user_type='FACULTY')
                    
                    # Check if already added
                    if SubEventFaculty.objects.filter(
                        faculty=faculty,
                        sub_event=sub_event
                    ).exists():
                        results['failed'].append({
                            'email': email,
                            'reason': 'Already added to this sub-event'
                        })
                        continue
                    
                    # Add faculty to sub-event
                    sub_event_faculty = SubEventFaculty.objects.create(
                        faculty=faculty,
                        sub_event=sub_event,
                        is_active=True
                    )
                    
                    results['success'].append({
                        'email': email,
                        'id': sub_event_faculty.id
                    })
                    
                except User.DoesNotExist:
                    results['failed'].append({
                        'email': email,
                        'reason': 'Faculty not found'
                    })
                except Exception as e:
                    results['failed'].append({
                        'email': email,
                        'reason': str(e)
                    })
            
            return Response({
                'message': 'Faculty assignment process completed',
                'results': results
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def faculty_list(self, request, pk=None):
        """Get list of faculty assigned to this sub-event"""
        sub_event = self.get_object()
        faculty_assignments = SubEventFaculty.objects.filter(
            sub_event=sub_event,
            is_active=True
        ).select_related('faculty')
        
        serializer = SubEventFacultySerializer(faculty_assignments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def round_participants(self, request, **kwargs):
        """Get participants for each round"""
        sub_event = self.get_object()
        round_number = request.query_params.get('round', sub_event.current_round)

        heats = EventHeat.objects.filter(
            sub_event=sub_event,
            round_number=round_number
        ).prefetch_related(
            'participants',
            'participants__team_members'
        )

        heat_data = []
        for heat in heats:
            participants = []
            for registration in heat.participants.all():
                participants.append({
                    'registration_id': registration.id,
                    'team_members': [{
                        'id': member.id,
                        'name': f"{member.first_name} {member.last_name}",
                        'email': member.email,
                    } for member in registration.team_members.all()],
                    'scores': EventScore.objects.filter(
                        event_registration=registration,
                        round_number=round_number,
                        heat=heat
                    ).values('position', 'time_taken', 'total_score', 'qualified_for_next')
                })

            heat_data.append({
                'heat_number': heat.heat_number,
                'status': heat.status,
                'scheduled_time': heat.scheduled_time,
                'participants': participants
            })

        return Response({
            'round_number': round_number,
            'heats': heat_data
        })

    @action(detail=True, methods=['post'])
    def register_team(self, request, pk=None):
        """Register a team/individual for the sub-event"""
        sub_event = self.get_object()
        
        # Validation logic here
        team_data = request.data
        
        try:
            registration = EventRegistration.objects.create(
                sub_event=sub_event,
                team_leader=request.user,
                team_name=team_data.get('team_name'),
                department=team_data.get('department'),
                year=team_data.get('year'),
                division=team_data.get('division')
            )
            
            # Add team members
            if team_data.get('team_members'):
                registration.team_members.set(team_data['team_members'])
            
            return Response(EventRegistrationSerializer(registration).data)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    # @action(detail=True, methods=['post'])
    # def submit_scores(self, request, pk=None):
    #     """Submit scores for participants"""
    #     sub_event = self.get_object()
    #     scores_data = request.data.get('scores', [])
        
    #     results = []
    #     for score_data in scores_data:
    #         try:
    #             score = EventScore.objects.create(
    #                 sub_event=sub_event,
    #                 event_registration_id=score_data['registration_id'],
    #                 judge=request.user,
    #                 total_score=score_data['total_score'],
    #                 criteria_scores=score_data.get('criteria_scores', {}),
    #                 remarks=score_data.get('remarks')
    #             )
    #             results.append(EventScoreSerializer(score).data)
    #         except Exception as e:
    #             results.append({'error': str(e)})
        
    #     return Response(results)

    @action(detail=True, methods=['get'])
    def registrations(self, request, pk=None):
        """Get all registrations for this sub-event"""
        sub_event = self.get_object()
        registrations = EventRegistration.objects.filter(sub_event=sub_event)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            registrations = registrations.filter(status=status_filter)
            
        return Response(EventRegistrationSerializer(registrations, many=True).data)

    @action(detail=True, methods=['get'] , url_path='get-scores')
    def get_scores(self, request, **kwargs):
        """Get scores for this sub-event"""
        sub_event = self.get_object()
        scores = EventScore.objects.filter(sub_event=sub_event)
        
        return Response(EventScoreSerializer(scores, many=True).data)

    @action(detail=True, methods=['post'])
    def update_stage(self, request, pk=None):
        """Update the current stage of the sub-event"""
        sub_event = self.get_object()
        new_stage = request.data.get('stage')
        
        if new_stage not in dict(SubEvent.EVENT_STAGES).keys():
            return Response({'error': 'Invalid stage'}, status=400)
            
        sub_event.current_stage = new_stage
        sub_event.save()
        
        return Response(SubEventSerializer(sub_event).data)
    @action(detail=True, methods=['post'], url_path='create-heat')
    def create_heat(self, request, **kwargs):
        """Create a new heat for the sub-event"""
        try:
            sub_event = self.get_object()
            stage = request.data.get('stage')
            round_number = request.data.get('round_number')
            
            if not stage or not round_number:
                return Response({
                    'error': 'stage and round_number are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get the next heat number for this specific stage and round
            existing_heats = EventHeat.objects.filter(
                sub_event=sub_event,
                stage=stage,
                round_number=round_number
            )
            next_heat_number = existing_heats.count() + 1

            # Create new heat with provided data
            heat_data = {
                **request.data,
                'sub_event': sub_event.id,
                'heat_number': next_heat_number,
                'heat_name': request.data.get('heat_name', f"Heat {next_heat_number}")
            }
            
            serializer = EventHeatSerializer(data=heat_data)
            if serializer.is_valid():
                heat = serializer.save()
                
                return Response({
                    'message': f'Heat {next_heat_number} created successfully for {stage} round {round_number}',
                    'heat': serializer.data,
                    'total_heats_in_round': next_heat_number
                }, status=status.HTTP_201_CREATED)
                
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['post'])
    def promote_participants(self, request, pk=None):
        """Promote selected participants to the next round"""
        current_heat = self.get_object()
        participant_ids = request.data.get('participant_ids', [])
        next_stage = request.data.get('next_stage')
        next_round = request.data.get('next_round')
        
        if not participant_ids:
            return Response({
                'error': 'No participants selected for promotion'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a new heat for the next round
        existing_heats = EventHeat.objects.filter(
            sub_event=current_heat.sub_event,
            stage=next_stage,
            round_number=next_round
        ).count()
        
        new_heat = EventHeat.objects.create(
            sub_event=current_heat.sub_event,
            stage=next_stage,
            round_number=next_round,
            heat_name=f"Heat {existing_heats + 1}",
            schedule=request.data.get('schedule'),
            venue=request.data.get('venue'),
            max_participants=len(participant_ids),
            status='PENDING'
        )
        
        # Move selected participants to the new heat
        for participant_id in participant_ids:
            participant = get_object_or_404(HeatParticipant, id=participant_id)
            HeatParticipant.objects.create(
                heat=new_heat,
                registration=participant.registration
            )
        
        return Response({
            'message': f'{len(participant_ids)} participants promoted to {next_stage} round {next_round}',
            'new_heat': EventHeatSerializer(new_heat).data
        })

    @action(detail=True, methods=['get'])
    def heat_scores(self, request, pk=None):
        """Get scores for all participants in a heat"""
        heat = self.get_object()
        scores = EventScore.objects.filter(heat=heat).select_related(
            'event_registration', 'judge'
        )
        
        # Group scores by participant
        participant_scores = {}
        for score in scores:
            reg_id = score.event_registration.id
            if reg_id not in participant_scores:
                participant_scores[reg_id] = {
                    'registration': score.event_registration,
                    'scores': [],
                    'average_score': 0
                }
            participant_scores[reg_id]['scores'].append(score)
        
        # Calculate averages
        for reg_id in participant_scores:
            scores = participant_scores[reg_id]['scores']
            total = sum(score.total_score for score in scores)
            participant_scores[reg_id]['average_score'] = total / len(scores)
        
        # Sort by average score
        sorted_scores = dict(sorted(
            participant_scores.items(),
            key=lambda x: x[1]['average_score'],
            reverse=True
        ))
        
        return Response({
            'heat_details': EventHeatSerializer(heat).data,
            'participant_scores': sorted_scores
        })

    @action(detail=True, methods=['post'] , url_path='assign-participants-to-heat')
    def assign_participants_to_heat(self, request, **kwargs):
        """Assign participants to a specific heat"""
        heat_id = request.data.get('heat_id')
        registration_ids = request.data.get('registration_ids', [])
        
        if not heat_id or not registration_ids:
            return Response({
                'error': 'heat_id and registration_ids are required'
            }, status=400)
            
        try:
            heat = EventHeat.objects.get(id=heat_id, sub_event_id=kwargs['id'])
            
            # Validate max participants
            if heat.max_participants > 0:
                current_count = heat.heatparticipant_set.count()
                if current_count + len(registration_ids) > heat.max_participants:
                    return Response({
                        'error': 'Exceeds maximum participants allowed'
                    }, status=400)
            
            # Add participants to heat
            for reg_id in registration_ids:
                HeatParticipant.objects.create(
                    heat=heat,
                    registration_id=reg_id
                )
            
            return Response(EventHeatSerializer(heat).data)
        except EventHeat.DoesNotExist:
            return Response({'error': 'Heat not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
        
    @action(detail=True, methods=['get'] , url_path='assigned-faculty')
    def assigned_faculty(self, request, **kwargs):
        """Get all faculty assigned to this sub-event"""
        sub_event = self.get_object()
        assignments = SubEventFaculty.objects.filter(
            sub_event=sub_event,
            is_active=True
        ).select_related('faculty')
        
        faculty_data = []
        for assignment in assignments:
            faculty = assignment.faculty
            faculty_data.append({
                'id': faculty.id,
                'name': f"{faculty.first_name} {faculty.last_name}",
                'email': faculty.email,
                'department': faculty.department,
                'assigned_at': assignment.assigned_at
            })
        
        return Response(faculty_data)
    @action(detail=True, methods=['get'])
    def get_scoring_criteria(self, request, **kwargs):
        """Get scoring criteria for a sub-event"""
        try:
            sub_event = get_object_or_404(SubEvent, id=kwargs['id'])
            
            # Get the scoring criteria from the related model
            scoring_criteria = None
            criteria = {}
            
            if sub_event.scoring_criteria:
                scoring_criteria = EventCriteria.objects.get(id=sub_event.scoring_criteria.id)
                # The criteria is already in the correct format, just use it directly
                criteria = scoring_criteria.criteria
            
            return Response({
                'sub_event_id': sub_event.id,
                'name': sub_event.name,
                'scoring_type': sub_event.scoring_type,
                'criteria': criteria,
                'allow_negative_marking': sub_event.allow_negative_marking,
                'scoring_criteria_id': scoring_criteria.id if scoring_criteria else None,
                'scoring_criteria_name': scoring_criteria.name if scoring_criteria else None
            })
        except EventCriteria.DoesNotExist:
            return Response(
                {'error': 'Scoring criteria not found for this sub-event'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
        )
    @action(detail=True, methods=['get'], url_path='get-heats')
    def get_heats(self, request, **kwargs):  # Change to use **kwargs
        """Get all heats for the sub-event with filters"""
        sub_event = self.get_object()
        heats = EventHeat.objects.filter(sub_event=sub_event)
        
        # Apply filters
        stage = request.query_params.get('stage')
        round_number = request.query_params.get('round')
        status = request.query_params.get('status')
        
        if stage:
            heats = heats.filter(stage=stage)
        if round_number:
            heats = heats.filter(round_number=round_number)
        if status:
            heats = heats.filter(status=status)
            
        return Response(EventHeatSerializer(heats, many=True).data)

    @action(detail=True, methods=['get'] , url_path='get-available-participants')
    def get_available_participants(self, request, **kwargs):
        """Get participants not assigned to any heat in the current stage"""
        sub_event = self.get_object()
        stage = request.query_params.get('stage')
        round_number = request.query_params.get('round')
        
        if not stage:
            return Response({'error': 'stage parameter is required'}, status=400)
            
        # Get all participants already assigned to heats
        assigned_participants = HeatParticipant.objects.filter(
            heat__sub_event=sub_event,
            heat__stage=stage,
            heat__round_number=round_number
        ).values_list('registration_id', flat=True)
        
        # Get available participants
        available = EventRegistration.objects.filter(
            sub_event=sub_event,
            status='APPROVED'
        ).exclude(
            id__in=assigned_participants
        )
        
        return Response(EventRegistrationSerializer(available, many=True).data)
    
    @action(detail=True, methods=['get'])
    def leaderboard(self, request, **kwargs):
        """Get leaderboard for this sub-event"""
        sub_event = self.get_object()
        stage = request.query_params.get('stage')
        round_number = request.query_params.get('round')
        
        scores = EventScore.objects.filter(
            sub_event=sub_event,
            stage=stage,
            round_number=round_number
        ).select_related('event_registration')
        
        # Group by registration and get highest score
        rankings = {}
        for score in scores:
            reg_id = score.event_registration_id
            if reg_id not in rankings or score.total_score > rankings[reg_id]['total_score']:
                rankings[reg_id] = {
                    'position': score.position,
                    'registration_id': reg_id,
                    'team_name': score.event_registration.team_name,
                    'total_score': score.total_score,
                    'qualified': score.qualified_for_next
                }
        
        # Sort by total score
        sorted_rankings = sorted(
            rankings.values(),
            key=lambda x: x['total_score'],
            reverse=True
        )
        
        return Response({
            'stage': stage,
            'round': round_number,
            'rankings': sorted_rankings
        })

class EventHeatViewSet(viewsets.ModelViewSet):
    queryset = EventHeat.objects.all()
    serializer_class = EventHeatSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = EventHeat.objects.all()
        
        # Filter based on user role
        if user.user_type == 'COUNCIL_MEMBER':
            # Get heats for events where user is sub_head
            queryset = queryset.filter(sub_event__sub_heads=user)
        elif user.user_type == 'FACULTY':
            # Get heats where faculty is judge
            queryset = queryset.filter(sub_event__subeventfaculty__faculty=user)
            
        # Apply additional filters
        sub_event = self.request.query_params.get('sub_event', None)
        status = self.request.query_params.get('status', None)
        round_type = self.request.query_params.get('round_type', None)
        
        if sub_event:
            queryset = queryset.filter(sub_event_id=sub_event)
        if status:
            queryset = queryset.filter(status=status)
        if round_type:
            queryset = queryset.filter(round_type=round_type)
            
        return queryset.distinct()

    @action(detail=False, methods=['get'])
    def my_heats(self, request):
        """Get heats based on user's role and involvement"""
        user = request.user
        heats = []
        
        if user.user_type == 'COUNCIL_MEMBER':
            # Get heats for events where user is sub_head
            heats = self.get_queryset().filter(sub_event__sub_heads=user)
        elif user.user_type == 'FACULTY':
            # Get heats where faculty is judge
            heats = self.get_queryset().filter(sub_event__subeventfaculty__faculty=user)
        elif user.user_type == 'STUDENT':
            # Get heats where student is participating
            heats = self.get_queryset().filter(
                heatparticipant__registration__team_leader=user
            )
        
        serializer = self.get_serializer(heats, many=True)
        return Response({
            'count': len(heats),
            'results': serializer.data
        })

    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """Get participants for a specific heat"""
        heat = self.get_object()
        participants = heat.heatparticipant_set.all()
        from .serializers import HeatParticipantSerializer
        serializer = HeatParticipantSerializer(participants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update heat status"""
        heat = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['PENDING', 'IN_PROGRESS', 'COMPLETED']:
            return Response({'error': 'Invalid status'}, status=400)
            
        heat.status = new_status
        heat.save()
        
        return Response(EventHeatSerializer(heat).data)

    @action(detail=True, methods=['post'] , url_path='remove-participants')
    def remove_participants(self, request, **kwargs):
        """Remove participants from heat"""
        heat = self.get_object()
        registration_ids = request.data.get('registration_ids', [])
        
        if not registration_ids:
            return Response({'error': 'registration_ids required'}, status=400)
            
        HeatParticipant.objects.filter(
            heat=heat,
            registration_id__in=registration_ids
        ).delete()
        
        return Response({'message': 'Participants removed successfully'})

    @action(detail=True, methods=['get'] , url_path='get-participants')
    def get_participants(self, request, **kwargs):
        """Get all participants in this heat"""
        heat = self.get_object()
        participants = HeatParticipant.objects.filter(heat=heat)
        
        return Response(HeatParticipantSerializer(participants, many=True).data)

    @action(detail=False, methods=['post'])
    def generate_heats(self, request):
        """Generate heats for a round"""
        sub_event_id = request.data.get('sub_event')
        round_number = request.data.get('round_number')
        participants_per_heat = request.data.get('participants_per_heat', 5)
        
        sub_event = get_object_or_404(SubEvent, id=sub_event_id)
        
        try:
            with transaction.atomic():
                # Get qualified participants from previous round
                if round_number == 1:
                    participants = EventRegistration.objects.filter(
                        sub_event=sub_event,
                        status='APPROVED'
                    )
                else:
                    participants = EventRegistration.objects.filter(
                        sub_event=sub_event,
                        heatparticipant__heat__round_number=round_number-1,
                        heatparticipant__qualified_for_next=True
                    ).distinct()
                
                # Shuffle participants
                participants = list(participants)
                random.shuffle(participants)
                
                # Create heats
                total_participants = len(participants)
                num_heats = (total_participants + participants_per_heat - 1) // participants_per_heat
                
                heats = []
                for heat_number in range(1, num_heats + 1):
                    heat = EventHeat.objects.create(
                        sub_event=sub_event,
                        stage=sub_event.current_stage,
                        round_number=round_number,
                        heat_number=heat_number,
                        max_participants=participants_per_heat,
                        schedule=timezone.now() + timezone.timedelta(hours=1)  # Default schedule
                    )
                    heats.append(heat)
                
                # Assign participants to heats
                for idx, participant in enumerate(participants):
                    heat_idx = idx // participants_per_heat
                    if heat_idx < len(heats):
                        HeatParticipant.objects.create(
                            heat=heats[heat_idx],
                            registration=participant
                        )
                
                return Response({
                    'message': f'Generated {len(heats)} heats',
                    'heats': EventHeatSerializer(heats, many=True).data
                })
                
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def update_heat_results(self, request, pk=None):
        """Update results for a heat"""
        heat = self.get_object()
        results = request.data.get('results', [])
        
        try:
            with transaction.atomic():
                for result in results:
                    participant = get_object_or_404(
                        HeatParticipant,
                        heat=heat,
                        registration_id=result['registration_id']
                    )
                    participant.position = result.get('position')
                    participant.qualified_for_next = result.get('qualified', False)
                    participant.remarks = result.get('remarks')
                    participant.save()
                
                # Update heat status
                heat.status = 'COMPLETED'
                heat.save()
                
                # Check if all heats in round are completed
                all_completed = EventHeat.objects.filter(
                    sub_event=heat.sub_event,
                    round_number=heat.round_number
                ).exclude(status='COMPLETED').count() == 0
                
                if all_completed:
                    # Trigger next round generation or finalize results
                    pass
                
                return Response({'message': 'Heat results updated successfully'})
                
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    # 1. Get Specific Heat
    @action(detail=True, methods=['get'])
    def get_heat_details(self, request, pk=None):
        """Get specific heat details with participants"""
        try:
            heat = get_object_or_404(EventHeat, id=pk)
            
            participants = HeatParticipant.objects.filter(heat=heat).select_related(
                'registration',
                'registration__sub_event',
                'registration__team_leader'  # Add team_leader for solo events
            ).prefetch_related(
                'registration__team_members'  # Add team members for team events
            )
            
            data = {
                'heat_id': heat.id,
                'stage': heat.stage,
                'round_number': heat.round_number,
                'heat_number': heat.heat_number,
                'schedule': heat.schedule,
                'venue': heat.venue,
                'status': heat.status,
                'participants': []
            }
            
            for p in participants:
                registration = p.registration
                participant_data = {
                    'registration_id': registration.id,
                    'department': registration.department,
                    'year': registration.year,
                    'division': registration.division,
                    'position': p.position,
                    'scores': []
                }
                
                # Handle name based on participation type
                if registration.sub_event.participation_type == 'SOLO':
                    # For solo events, use team leader's name
                    if registration.team_members.first():
                        participant_data['participant_name'] = (
                            f"{registration.team_members.first().first_name} {registration.team_members.first().last_name}".strip()
                        )
                        participant_data['team_name'] = None
                else:
                    # For team events, use team name
                    participant_data['team_name'] = registration.team_name
                    participant_data['participant_name'] = None
                
                data['participants'].append(participant_data)
            
            # Add scores if heat is completed or in progress
            if heat.status in ['IN_PROGRESS', 'COMPLETED']:
                scores = EventScore.objects.filter(heat=heat).select_related('judge')
                for score in scores:
                    participant = next(
                        (p for p in data['participants'] 
                         if p['registration_id'] == score.event_registration_id),
                        None
                    )
                    if participant:
                        # Skip empty scores
                        if not score.criteria_scores and score.total_score is None:
                            continue
                        
                        participant['scores'].append({
                            'judge_id': score.judge.id,
                            'judge_name': f"{score.judge.first_name} {score.judge.last_name}".strip(),
                            'criteria_scores': score.criteria_scores,
                            'total_score': score.total_score,
                            'aura_points': score.aura_points,
                            # 'submitted_at': score.created_at
                        })
            
            return Response(data)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    # 2. Get Scoring Criteria
    

    # 3. View Faculty Scores
    @action(detail=True, methods=['get'])
    def view_faculty_scores(self, request, pk=None):
        """View scores submitted by faculty for a heat"""
        try:
            heat = get_object_or_404(EventHeat, id=pk)
            scores = EventScore.objects.filter(heat=heat).select_related(
                'judge', 
                'event_registration',
                'event_registration__sub_event'
            )
            
            # Group scores by judge
            scores_by_judge = {}
            for score in scores:
                judge_name = f"{score.judge.first_name} {score.judge.last_name}".strip()
                if judge_name not in scores_by_judge:
                    scores_by_judge[judge_name] = []
                
                registration = score.event_registration
                
                # Determine participant name based on event type
                if registration.sub_event.participation_type == 'SOLO':
                    if registration.team_leader:
                        participant_name = f"{registration.team_leader.first_name} {registration.team_leader.last_name}".strip()
                    else:
                        participant_name = "Unknown Participant"
                else:
                    participant_name = registration.team_name or "Unknown Team"
                
                # Skip empty scores
                if not score.criteria_scores and score.total_score is None:
                    continue
                    
                scores_by_judge[judge_name].append({
                    'participant_name': participant_name,
                    'registration_id': registration.id,
                    'criteria_scores': score.criteria_scores,
                    'total_score': score.total_score,
                    'aura_points': score.aura_points,
                    # 'submitted_at': score.created_at,
                    'department': registration.department,
                    'year': registration.year,
                    'division': registration.division
                })
            
            return Response({
                'heat_id': heat.id,
                'sub_event': heat.sub_event.name,
                'stage': heat.stage,
                'round_number': heat.round_number,
                'heat_number': heat.heat_number,
                'status': heat.status,
                'scores_by_judge': scores_by_judge
            })
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    # 4. View Final Results
    @action(detail=True, methods=['get'])
    def view_final_results(self, request, pk=None):
        """View final results for a heat"""
        try:
            heat = get_object_or_404(EventHeat, id=pk)
            
            if heat.status != 'COMPLETED':
                return Response({
                    'error': 'Heat is not completed yet'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get average scores and positions
            final_scores = EventScore.objects.filter(
                heat=heat
            ).values(
                'event_registration'
            ).annotate(
                avg_score=Avg('total_score'),
                aura_points=Max('aura_points'),  # Get the aura points directly from scores
                final_position=Min('position')  # All scores for same registration should have same position
            ).order_by('final_position', '-avg_score')
            
            results = []
            for score in final_scores:
                registration = EventRegistration.objects.select_related(
                    'team_leader',
                    'sub_event'
                ).get(id=score['event_registration'])
                
                # Determine participant name based on event type
                if registration.sub_event.participation_type == 'SOLO':
                    if registration.team_members.first():
                        participant_name = f"{registration.team_members.first().first_name} {registration.team_members.first().last_name}".strip()
                    else:
                        participant_name = "Unknown Participant"
                    team_name = None
                else:
                    team_name = registration.team_name
                    participant_name = None
                
                results.append({
                    'position': score['final_position'],
                    'registration_id': registration.id,
                    'participant_name': participant_name,
                    'team_name': team_name,
                    'department': registration.department,
                    'year': registration.year,
                    'division': registration.division,
                    'average_score': round(score['avg_score'], 2) if score['avg_score'] else None,
                    'aura_points': score['aura_points'] or 0  # Use aura points from aggregation
                })
            
            return Response({
                'heat_id': heat.id,
                'sub_event': heat.sub_event.name,
                'stage': heat.stage,
                'round_number': heat.round_number,
                'heat_number': heat.heat_number,
                'status': heat.status,
                'results': results
            })
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class EventRegistrationViewSet(viewsets.ModelViewSet):
    queryset = EventRegistration.objects.all()
    serializer_class = EventRegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = EventRegistration.objects.all()
        
        # Filter parameters
        sub_event = self.request.query_params.get('sub_event')
        department = self.request.query_params.get('department')
        year = self.request.query_params.get('year')
        division = self.request.query_params.get('division')
        status = self.request.query_params.get('status')
        event = self.request.query_params.get('event')
        
        if sub_event:
            queryset = queryset.filter(sub_event_id=sub_event)
        if department:
            queryset = queryset.filter(team_leader__department=department)
        if year:
            queryset = queryset.filter(team_leader__year_of_study=year)
        if division:
            queryset = queryset.filter(team_leader__division=division)
        if status:
            queryset = queryset.filter(status=status)
        if event:
            queryset = queryset.filter(sub_event__event_id=event)
            
        return queryset.select_related(
            'sub_event', 
            'team_leader'
        ).prefetch_related('team_members')

    @action(detail=False, methods=['get'])
    def get_by_filters(self, request):
        """Get registrations with multiple filters"""
        registrations = EventRegistration.objects.all()
        
        # Apply filters
        event = request.query_params.get('event')
        sub_event = request.query_params.get('sub_event')
        department = request.query_params.get('department')
        year = request.query_params.get('year')
        division = request.query_params.get('division')
        status = request.query_params.get('status')
        has_files = request.query_params.get('has_files')
        search = request.query_params.get('search')
        
        if event:
            registrations = registrations.filter(sub_event__event_id=event)
        if sub_event:
            registrations = registrations.filter(sub_event_id=sub_event)
        if department:
            registrations = registrations.filter(department=department)
        if year:
            registrations = registrations.filter(year=year)
        if division:
            registrations = registrations.filter(division=division)
        if status:
            registrations = registrations.filter(status=status)
        if has_files is not None:
            registrations = registrations.filter(has_submitted_files=has_files)
        if search:
            registrations = registrations.filter(
                Q(team_name__icontains=search) |
                Q(team_leader__email__icontains=search)
            )
        
        return Response(EventRegistrationSerializer(registrations, many=True).data)
    
    @action(detail=False, methods=['get'])
    def my_registrations(self, request):
            """Get all registrations for the logged-in user with filters"""
            try:
                registrations = EventRegistration.objects.filter(
                    Q(team_leader=request.user) | 
                    Q(team_members=request.user)
                ).distinct()

                # Apply filters
                event = request.query_params.get('event')
                sub_event = request.query_params.get('sub_event') 
                status_filter = request.query_params.get('status')  # Renamed to avoid conflict
                stage = request.query_params.get('stage')
                has_files = request.query_params.get('has_files')
                search = request.query_params.get('search')

                if event:
                    registrations = registrations.filter(sub_event__event_id=event)
                if sub_event:
                    registrations = registrations.filter(sub_event_id=sub_event)
                if status_filter:
                    registrations = registrations.filter(status=status_filter)
                if stage:
                    registrations = registrations.filter(current_stage=stage)
                if has_files is not None:
                    registrations = registrations.filter(has_submitted_files=has_files)
                if search:
                    registrations = registrations.filter(
                        Q(team_name__icontains=search) |
                        Q(sub_event__name__icontains=search)
                    )

                # Sort by registration_date instead of created_at
                sort_by = request.query_params.get('sort_by', '-registration_date')
                registrations = registrations.order_by(sort_by)

                # Optimize queries
                registrations = registrations.select_related(
                    'sub_event', 
                    'team_leader'
                ).prefetch_related('team_members')

                serializer = EventRegistrationSerializer(registrations, many=True)
                return Response(serializer.data)

            except Exception as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    
    @action(detail=False, methods=['get'])
    def get_team_submissions(self, request):
        """Get all team submissions with filters"""
        registrations = EventRegistration.objects.filter(has_submitted_files=True)
        
        event = request.query_params.get('event')
        sub_event = request.query_params.get('sub_event')
        status = request.query_params.get('status')
        
        if event:
            registrations = registrations.filter(sub_event__event_id=event)
        if sub_event:
            registrations = registrations.filter(sub_event_id=sub_event)
        if status:
            registrations = registrations.filter(status=status)
            
        return Response(EventRegistrationSerializer(registrations, many=True).data)
    
    @action(detail=False, methods=['get'])
    def get_by_registration_number(self, request):
        reg_number = request.query_params.get('registration_number')
        if not reg_number:
            return Response(
                {"error": "Registration number is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        registration = get_object_or_404(EventRegistration, registration_number=reg_number)
        serializer = self.get_serializer(registration)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        sub_event = get_object_or_404(SubEvent, id=request.data.get('sub_event'))
        
        # Validate registration window
        if not self._validate_registration_window(sub_event):
            return Response({"error": "Registration is not open"}, status=400)
        
        
        # Validate gender restrictions
        if not self._validate_gender_participation(request.user, sub_event):
            return Response(
                {"error": f"This event is restricted to {sub_event.get_gender_participation_display()} participants"}, 
                status=400
            )

        # Prepare registration data
        registration_data = request.data.copy()
        
        if sub_event.participation_type == 'SOLO':
            # Solo event: only one participant, no team leader or team name
            registration_data.pop('team_leader', None)
            registration_data.pop('team_name', None)
            registration_data.pop('team_members', None)  # Will add current user later
        else:
            # Team event: requires team name and optionally team members
            if not registration_data.get('team_name'):
                return Response({"error": "Team name is required"}, status=400)
            registration_data['team_leader'] = request.user.id

        # Create registration
        serializer = self.get_serializer(data=registration_data)
        serializer.is_valid(raise_exception=True)
        registration = serializer.save()

        # Add participants
        if sub_event.participation_type == 'SOLO':
            registration.team_members.add(request.user)
        else:
            # Add team leader and members
            registration.team_members.add(request.user)
            team_members = registration_data.get('team_members', [])
            if team_members:
                registration.team_members.add(*team_members)

        # Send confirmation email
        try:
            self._send_registration_email(registration , sub_event )
        except Exception as e:
            print(f"Failed to send confirmation email: {str(e)}")

        return Response(serializer.data, status=201)

    # def create(self, request, *args, **kwargs):
    #     """Create registration with current user as team leader"""
    #     try:
    #         # Get the sub_event and validate it exists
    #         sub_event = get_object_or_404(SubEvent, id=request.data.get('sub_event'))
            
    #         # Create registration data
    #         registration_data = {
    #             'sub_event_id': sub_event.id,
    #             'team_leader_id': request.user.id,  # Set team leader ID explicitly
    #             'department': request.data.get('department'),
    #             'year': request.data.get('year'),
    #             'division': request.data.get('division'),
    #             'team_name': request.data.get('team_name'),
    #             'current_stage': 'REGISTRATION',
    #             'status': 'PENDING'
    #         }
            
    #         # Create registration
    #         registration = EventRegistration.objects.create(**registration_data)
            
    #         # Handle team members based on event type
    #         if sub_event.participation_type == 'SOLO':
    #             # For solo events, don't add any team members
    #             pass
    #         elif sub_event.participation_type == 'TEAM':
    #             # For team events, add team members if provided
    #             team_members = request.data.get('team_members', [])
    #             if team_members:
    #                 registration.team_members.set(team_members)
            
    #         # Refresh and serialize
    #         registration.refresh_from_db()
    #         serializer = self.get_serializer(registration)
            
    #         return Response(
    #             serializer.data,
    #             status=status.HTTP_201_CREATED
    #         )
            
    #     except Exception as e:
    #         return Response({
    #             'error': str(e)
    #         }, status=status.HTTP_400_BAD_REQUEST)
        
    # def create(self, request, *args, **kwargs):
    #     try:
    #         sub_event = get_object_or_404(SubEvent, id=request.data.get('sub_event'))
            
    #         # Validate registration window
    #         if not self._validate_registration_window(sub_event):
    #             return Response({"error": "Registration is not open"}, status=400)
            
    #         # Validate gender restrictions
    #         if not self._validate_gender_participation(request.user, sub_event):
    #             return Response(
    #                 {"error": f"This event is restricted to {sub_event.get_gender_participation_display()} participants"}, 
    #                 status=400
    #             )

    #         # Create base registration data
    #         registration_data = {
    #             'sub_event': sub_event.id,
    #             'team_leader': request.user,  # Always set current user as team leader
    #             'department': request.data.get('department'),
    #             'year': request.data.get('year'),
    #             'division': request.data.get('division'),
    #             'current_stage': 'REGISTRATION',
    #             'status': 'PENDING'
    #         }

    #         # Handle team vs solo events
    #         if sub_event.participation_type == 'TEAM':
    #             if not request.data.get('team_name'):
    #                 return Response({"error": "Team name is required"}, status=400)
    #             registration_data['team_name'] = request.data.get('team_name')

    #         # Create registration
    #         serializer = self.get_serializer(data=registration_data)
    #         serializer.is_valid(raise_exception=True)
    #         registration = serializer.save()

    #         # Handle team members
    #         if sub_event.participation_type == 'TEAM':
    #             # For team events, add other team members if provided
    #             team_members = request.data.get('team_members', [])
    #             if team_members:
    #                 # Validate team members exist
    #                 existing_users = User.objects.filter(id__in=team_members).values_list('id', flat=True)
    #                 invalid_ids = set(team_members) - set(existing_users)
                    
    #                 if invalid_ids:
    #                     registration.delete()
    #                     return Response({
    #                         'error': f'Invalid team member IDs: {list(invalid_ids)}'
    #                     }, status=status.HTTP_400_BAD_REQUEST)
                    
    #                 registration.team_members.add(*team_members)

    #         # Send confirmation email
    #         try:
    #             self._send_registration_email(registration)
    #         except Exception as e:
    #             print(f"Failed to send confirmation email: {str(e)}")

    #         # Refresh and return
    #         registration.refresh_from_db()
    #         serializer = self.get_serializer(registration)
    #         return Response(serializer.data, status=201)

    #     except Exception as e:
    #         return Response({
    #             'error': str(e)
    #         }, status=status.HTTP_400_BAD_REQUEST)
        
    def _validate_registration_window(self, sub_event):
        current_time = timezone.now()
        if not sub_event.registration_start_time or not sub_event.registration_end_time:
            return False
        return sub_event.registration_start_time <= current_time <= sub_event.registration_end_time

    def _send_registration_email(self, registration , sub_event ):
        
        team_members = registration.team_members.all().select_related('department').values(
            'id',
            'first_name',
            'last_name',
            'email',
            'department',
            'year_of_study',
            'division'
        )
        
        # Add full name to each member
        for member in team_members:
            member['full_name'] = f"{member['first_name']} {member['last_name']}"

        context = {
            'registration': registration,
            'event': registration.sub_event.event,
            'sub_event': registration.sub_event,
            'team_members': team_members,
            'is_solo': registration.sub_event.participation_type == 'SOLO',
            'registration_number': registration.registration_number,
            'primary_contact': registration.get_primary_contact(),
            'participants': registration.get_all_participants(),
        }

        subject = f'Registration Confirmation - {registration.sub_event.name}'
        html_message = render_to_string('emails/registration_confirmation.html', context)
        plain_message = render_to_string('emails/registration_confirmation.txt', context)

        # Send to all participants
        for participant in registration.get_all_participants():
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[participant.email]
            )
            
    def _validate_gender_participation(self, user, sub_event):
        """Validate if user meets gender participation requirements"""
        if sub_event.gender_participation == 'ALL':
            return True
        
        user_gender = getattr(user, 'gender', None)  # Assuming user model has gender field
        if not user_gender:
            return False
            
        if sub_event.gender_participation == 'MALE' and user_gender.upper() != 'MALE':
            return False
        if sub_event.gender_participation == 'FEMALE' and user_gender.upper() != 'FEMALE':
            return False
            
        return True

    def _validate_team_gender(self, team_members, sub_event):
        """Validate gender requirements for all team members"""
        if sub_event.gender_participation == 'ALL':
            return True
            
        for member in team_members:
            if not self._validate_gender_participation(member, sub_event):
                return False
        return True

    @action(detail=True, methods=['POST'])
    def approve(self, request, pk=None):
        """
        Approve a registration
        POST /api/events/registrations/{id}/approve/
        """
        registration = self.get_object()
        
        # Check if already approved
        if registration.status == 'APPROVED':
            return Response(
                {"error": "Registration is already approved"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Update status
        registration.status = 'APPROVED'
        registration.save()
        
        # Send approval email
        try:
            self._send_status_update_email(registration, is_approved=True)
        except Exception as e:
            print(f"Failed to send approval email: {str(e)}")

        return Response({
            "message": "Registration approved successfully",
            "registration_number": registration.registration_number,
            "status": registration.status,
            "updated_at": timezone.now()
        })


    @action(detail=False, methods=['get'])
    def sub_event_registrations(self, request):
        """Get registrations for a specific sub-event with filters"""
        sub_event_id = request.query_params.get('sub_event_id')  # Get sub_event_id from query params
        department = request.query_params.get('department')
        year = request.query_params.get('year')
        division = request.query_params.get('division')
        status = request.query_params.get('status')  # e.g., 'PENDING', 'CONFIRMED'

        if not sub_event_id:
            return Response({'error': 'sub_event_id is required'}, status=400)

        # Filter registrations based on the provided parameters
        registrations = EventRegistration.objects.filter(sub_event_id=sub_event_id)

        if department:
            registrations = registrations.filter(department=department)
        if year:
            registrations = registrations.filter(year=year)
        if division:
            registrations = registrations.filter(division=division)
        if status:
            registrations = registrations.filter(status=status)

        # Serialize the data (assuming you have a serializer for EventRegistration)
        serializer = EventRegistrationSerializer(registrations, many=True)

        return Response(serializer.data)
    
    @action(detail=True, methods=['POST'])
    def reject(self, request, pk=None):
        """
        Reject a registration
        POST /api/events/registrations/{id}/reject/
        """
        registration = self.get_object()
        reason = request.data.get('reason', '')
        
        # Check if already rejected
        if registration.status == 'REJECTED':
            return Response(
                {"error": "Registration is already rejected"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Update status
        registration.status = 'REJECTED'
        registration.save()
        
        # Send rejection email
        try:
            self._send_status_update_email(registration, is_approved=False, reason=reason)
        except Exception as e:
            print(f"Failed to send rejection email: {str(e)}")

        return Response({
            "message": "Registration rejected successfully",
            "registration_number": registration.registration_number,
            "status": registration.status,
            "reason": reason,
            "updated_at": timezone.now()
        })

    def _send_status_update_email(self, registration, is_approved, reason=''):
        """Send email notification for approval/rejection"""
        context = {
            'registration': registration,
            'event': registration.sub_event.event,
            'sub_event': registration.sub_event,
            'is_solo': registration.sub_event.participation_type == 'SOLO',
            'is_approved': is_approved,
            'reason': reason,
            'primary_contact': registration.get_primary_contact(),
            'participants': registration.get_all_participants(),
        }

        template_prefix = 'approval' if is_approved else 'rejection'
        subject = f'Registration {"Approved" if is_approved else "Rejected"} - {registration.sub_event.name}'
        
        html_message = render_to_string(f'emails/{template_prefix}_notification.html', context)
        plain_message = render_to_string(f'emails/{template_prefix}_notification.txt', context)

        # Send to all participants
        for participant in registration.get_all_participants():
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[participant.email]
            )
            
    @action(detail=False, methods=['get'], url_path='available-team-members')
    def available_team_members(self, request):
        """Get list of users available for team selection"""
        sub_event_id = request.query_params.get('sub_event')
        if not sub_event_id:
            return Response(
                {"error": "sub_event parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            sub_event = SubEvent.objects.get(id=sub_event_id)
        except SubEvent.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)

        # Get users who haven't registered for this sub-event
        registered_users = EventRegistration.objects.filter(
            sub_event=sub_event
        ).values_list('team_members', flat=True)

        available_users = User.objects.exclude(
            id__in=registered_users
        ).exclude(
            id=request.user.id  # Exclude the current user
        )

        # Apply gender filter if event has gender restrictions
        if sub_event.gender_participation != 'ALL':
            available_users = available_users.filter(gender=sub_event.gender_participation)

        # Filter options
        department = request.query_params.get('department')
        year_of_study = request.query_params.get('year')  # Changed parameter name
        division = request.query_params.get('division')

        if department:
            available_users = available_users.filter(department=department)
        if year_of_study:  # Changed variable name
            available_users = available_users.filter(year_of_study=year_of_study)  # Changed field name
        if division:
            available_users = available_users.filter(division=division)

        # Convert to list of dictionaries with required fields
        available_users = list(available_users.values(
            'id', 
            'first_name', 
            'last_name', 
            'email', 
            'department', 
            'year_of_study',  # Changed field name
            'division'
        ))

        # Rename year_of_study to year in response for frontend compatibility
        for user in available_users:
            user['year'] = user.pop('year_of_study')

        return Response(available_users, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'] , url_path='scores')
    def get_scores(self, request,pk=None, **kwargs):
        registration = self.get_object() 
        scores = EventScore.objects.filter(event_registration=registration)
        return Response(EventScoreSerializer(scores, many=True).data)
    
    
    @action(detail=True, methods=['post'])
    def submit_files(self, request, pk=None):
        registration = self.get_object()
        files = request.FILES.getlist('files')
        file_types = request.POST.getlist('file_types')
        
        if not files:
            return Response(
                {'error': 'No files provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        for file, file_type in zip(files, file_types):
            SubmissionFile.objects.create(
                registration=registration,
                file=file,
                file_type=file_type
            )
        
        registration.has_submitted_files = True
        registration.save()
        
        return Response({'message': 'Files submitted successfully'})

class EventDrawViewSet(viewsets.ModelViewSet):
    queryset = EventDraw.objects.all()
    serializer_class = EventDrawSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def declare_winner(self, request, pk=None):
        draw = self.get_object()
        winner_id = request.data.get('winner_id')
        
        if winner_id not in [draw.team1.id, draw.team2.id]:
            return Response(
                {'error': 'Invalid winner'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        winner = EventRegistration.objects.get(id=winner_id)
        draw.winner = winner
        draw.save()
        
        # Update winner's stage if not in finals
        if draw.stage != 'FINALS':
            next_stages = {
                'PRELIMS': 'QUARTERS',
                'QUARTERS': 'SEMIS',
                'SEMIS': 'FINALS'
            }
            winner.current_stage = next_stages[draw.stage]
            winner.save()
        
        return Response({'message': 'Winner declared successfully'})

class EventScoreViewSet(viewsets.ModelViewSet):
    queryset = EventScore.objects.all()
    serializer_class = EventScoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = EventScore.objects.all()
        sub_event = self.request.query_params.get('sub_event', None)
        stage = self.request.query_params.get('stage', None)
        heat = self.request.query_params.get('heat', None)

        # If user is faculty, only show scores for their assigned sub-events
        if user.user_type == 'FACULTY':
            assigned_sub_events = user.judged_sub_events.all()
            queryset = queryset.filter(sub_event__in=assigned_sub_events)

        sub_event = self.request.query_params.get('sub_event', None)
        stage = self.request.query_params.get('stage', None)
        heat = self.request.query_params.get('heat', None)

        if sub_event:
            queryset = queryset.filter(sub_event_id=sub_event)
        if stage:
            queryset = queryset.filter(stage=stage)
        if heat:
            queryset = queryset.filter(heat_id=heat)

        return queryset.select_related(
            'sub_event',
            'event_registration',
            'judge',
            'heat'
        )

    def update(self, request, *args, **kwargs):
        score = self.get_object()
        
        # Update only allowed fields
        score.total_score = request.data.get('total_score', score.total_score)
        score.criteria_scores = request.data.get('criteria_scores', score.criteria_scores)
        score.remarks = request.data.get('remarks', score.remarks)
        score.qualified_for_next = request.data.get('qualified_for_next', score.qualified_for_next)
        score.save()
        
        return Response(EventScoreSerializer(score).data)
    
    @action(detail=False, methods=['get'])
    def heat_participants(self, request):
        """Get participants for scoring based on heat"""
        heat_id = request.query_params.get('heat')
        if not heat_id:
            return Response(
                {"error": "Heat ID required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        heat = get_object_or_404(EventHeat, id=heat_id)
        participants = HeatParticipant.objects.filter(heat=heat)
        
        return Response(HeatParticipantSerializer(participants, many=True).data)
    
    @action(detail=False, methods=['post'])
    def submit_scores(self, request):
        """Submit scores for multiple participants"""
        heat_id = request.data.get('heat_id')
        scores_data = request.data.get('scores', [])
        
        try:
            # Get the heat and verify it exists
            heat = get_object_or_404(EventHeat, id=heat_id)
            
            with transaction.atomic():
                created_scores = []
                for score_data in scores_data:
                    registration_id = score_data.get('registration_id')
                    criteria_scores = score_data.get('criteria_scores', {})
                    remarks = score_data.get('remarks', '')
                    
                    # Verify the registration exists in this heat
                    if not HeatParticipant.objects.filter(
                        heat=heat,
                        registration_id=registration_id
                    ).exists():
                        raise ValidationError(f"Registration {registration_id} not found in heat {heat_id}")
                    
                    # Calculate total score based on criteria weights
                    total_score = 0
                    for criterion, score in criteria_scores.items():
                        # You might want to get weights from sub_event criteria configuration
                        total_score += score  # For now, simple average
                    
                    total_score = total_score / len(criteria_scores) if criteria_scores else 0
                    
                    # Create score
                    score = EventScore.objects.create(
                        sub_event=heat.sub_event,
                        event_registration_id=registration_id,
                        heat=heat,
                        judge=request.user,
                        criteria_scores=criteria_scores,
                        total_score=total_score,
                        remarks=remarks
                    )
                    created_scores.append(score)
                
                return Response({
                    'message': 'Scores submitted successfully',
                    'heat_id': heat_id,
                    'scores_submitted': len(created_scores)
                })
                
        except EventHeat.DoesNotExist:
            return Response(
                {'error': 'Heat not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        user = self.request.user
        sub_event = serializer.validated_data['sub_event']

        # Check if user is assigned as faculty for this sub-event
        if user.user_type == 'FACULTY' and not SubEventFaculty.objects.filter(
            faculty=user,
            sub_event=sub_event,
            is_active=True
        ).exists():
            raise PermissionDenied("You are not assigned to judge this event")

        serializer.save(judge=user, updated_by=user)

    def perform_update(self, serializer):
        user = self.request.user
        sub_event = serializer.validated_data['sub_event']

        # Check if user is assigned as faculty for this sub-event
        if user.user_type == 'FACULTY' and not SubEventFaculty.objects.filter(
            faculty=user,
            sub_event=sub_event,
            is_active=True
        ).exists():
            raise PermissionDenied("You are not assigned to judge this event")

        serializer.save(updated_by=user)
        
    def create(self, request, *args, **kwargs):
        if request.user.user_type not in ['ADMIN', 'COUNCIL', 'FACULTY']:
            return Response(
                {'error': 'Unauthorized to add scores'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        sub_event = get_object_or_404(SubEvent, id=request.data.get('sub_event'))
        serializer = self.get_serializer(
            data=request.data,
            context={'sub_event': sub_event}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(judge=request.user, updated_by=request.user)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    # @action(detail=False, methods=['post'] , url_path='submit-score')
    # def submit_score(self, request):
        
    #     sub_event = get_object_or_404(SubEvent, id=request.data.get('sub_event'))
    #     """
    #     Submit scores for a participant/team
    #     """
    #     sub_event_id = request.data.get('sub_event')
    #     registration_id = request.data.get('registration')
        
    #     # Validate permissions
    #     if not self._can_submit_score(request.user, sub_event_id):
    #         return Response(
    #             {"error": "You are not authorized to submit scores for this event"},
    #             status=status.HTTP_403_FORBIDDEN
    #         )

    #     # Get or create score object
    #     score_data = {
    #         'sub_event': request.data.get('sub_event'),
    #         'event_registration': request.data.get('registration'),  # Changed from registration to event_registration
    #         'judge': request.user.id,  # Add judge ID explicitly
    #         'stage': request.data.get('stage'),
    #         'score_type': request.data.get('score_type'),
    #         'round_number': request.data.get('round_number'),
    #         'heat': request.data.get('heat'),
    #         'total_score': request.data.get('total_score'),
    #         'criteria_scores': request.data.get('criteria_scores', {}),
    #         'position': request.data.get('position'),
    #         'remarks': request.data.get('remarks'),
    #         'qualified_for_next': request.data.get('qualified_for_next', False)
    #     }

    #     serializer = EventScoreSerializer(
    #         data=score_data,
    #         context={'sub_event': sub_event, 'request': request}
    #     )
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def participant_scores(self, request):
        """
        Get scores for a specific participant/team
        """
        registration_id = request.query_params.get('registration')
        if not registration_id:
            return Response(
                {"error": "registration parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        scores = EventScore.objects.filter(
            event_registration_id=registration_id
        ).select_related('judge', 'sub_event')

        serializer = self.get_serializer(scores, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def event_leaderboard(self, request):
        """
        Get leaderboard for a specific sub-event
        """
        sub_event_id = request.query_params.get('sub_event')
        stage = request.query_params.get('stage')
        round_number = request.query_params.get('round')

        if not sub_event_id:
            return Response(
                {"error": "sub_event parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        scores = EventScore.objects.filter(
            sub_event_id=sub_event_id
        )

        if stage:
            scores = scores.filter(stage=stage)
        if round_number:
            scores = scores.filter(round_number=round_number)

        # Calculate average scores from all judges
        from django.db.models import Avg, Count
        leaderboard = scores.values(
            'event_registration',
            'event_registration__team_leader__first_name',
            'event_registration__team_name'
        ).annotate(
            average_score=Avg('total_score'),
            judge_count=Count('judge', distinct=True)
        ).order_by('-average_score')

        return Response(leaderboard)

    def _can_submit_score(self, user, sub_event_id):
        """Check if user can submit scores for this sub-event"""
        if user.user_type in ['ADMIN', 'COUNCIL']:
            return True
        
        if user.user_type == 'FACULTY':
            return SubEventFaculty.objects.filter(
                faculty=user,
                sub_event_id=sub_event_id,
                is_active=True
            ).exists()
        
        return False

    @action(detail=False, methods=['post'])
    def record_sports_results(self, request):
        """Record results for sports events"""
        heat_id = request.data.get('heat')
        results = request.data.get('results', [])
        
        try:
            heat = get_object_or_404(EventHeat, id=heat_id)
            sub_event = heat.sub_event
            
            # First, validate that all registration_ids exist in the heat
            heat_participants = HeatParticipant.objects.filter(heat=heat).values_list('registration_id', flat=True)
            
            for result in results:
                registration_id = result.get('registration_id')
                if registration_id not in heat_participants:
                    return Response(
                        {
                            'error': f'Registration ID {registration_id} not found in heat {heat_id}. '
                            f'Valid registrations are: {list(heat_participants)}'
                        }, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            with transaction.atomic():
                for result in results:
                    registration_id = result['registration_id']
                    position = result.get('position')
                    
                    # Get the actual registration from HeatParticipant
                    heat_participant = HeatParticipant.objects.get(
                        heat=heat,
                        registration_id=registration_id
                    )
                    
                    # Get the event registration
                    registration = EventRegistration.objects.get(id=registration_id)
                    
                    # Calculate AURA points
                    aura_points = 0
                    if position == 1:  # Winner
                        aura_points = sub_event.aura_points_winner
                    elif position == 2:  # Runner-up
                        aura_points = sub_event.aura_points_runner
                    
                    # Add match points if applicable
                    if (sub_event.match_points_enabled and 
                        position == 1 and 
                        heat.stage != 'FINALS'):
                        aura_points += 20
                    
                    # Create EventScore
                    event_score = EventScore.objects.create(
                        sub_event=sub_event,
                        event_registration_id=heat_participant.registration_id,
                        heat=heat,
                        position=position,
                        aura_points=aura_points,
                        judge=request.user
                    )
                    
                    # Update or create DepartmentScore
                    dept_score, created = DepartmentScore.objects.get_or_create(
                        department=registration.department,
                        year=registration.year,
                        division=registration.division,
                        sub_event=sub_event,
                        defaults={
                            'total_score': 0,
                            'aura_points': 0
                        }
                    )
                    
                    # Update department score
                    if position in [1, 2]:  # Only update for winners and runners-up
                        dept_score.aura_points = aura_points
                        # For sports events, total_score can be based on position
                        dept_score.total_score = 10 - position  # 1st gets 9, 2nd gets 8
                        dept_score.save()
                    
                    # Update heat participant position
                    heat_participant.position = position
                    heat_participant.save()
                
                # Update heat status
                heat.status = 'COMPLETED'
                heat.save()
                
                return Response({
                    'message': 'Sports results recorded successfully',
                    'heat_id': heat_id,
                    'results_recorded': len(results)
                })
                
        except EventHeat.DoesNotExist:
            return Response(
                {'error': f'Heat {heat_id} not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except HeatParticipant.DoesNotExist:
            return Response(
                {'error': 'Invalid registration ID for this heat'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except EventRegistration.DoesNotExist:
            return Response(
                {'error': 'Event registration not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def submit_cultural_scores(self, request):
        """Submit scores for cultural events"""
        heat_id = request.data.get('heat_id')
        scores_data = request.data.get('scores', [])
        
        try:
            heat = get_object_or_404(EventHeat, id=heat_id)
            sub_event = heat.sub_event
            criteria = sub_event.get_scoring_criteria()
            
            # Validate participants are in the heat
            heat_participants = HeatParticipant.objects.filter(heat=heat).values_list('registration_id', flat=True)
            
            # Calculate expected total scores
            total_judges = heat.sub_event.faculty_judges.count()
            total_participants = heat_participants.count()
            expected_total_scores = total_judges * total_participants
            
            # Get current scores submitted
            current_scores = EventScore.objects.filter(
                heat=heat
            ).values('judge', 'event_registration').distinct().count()
            
            # Check if this judge has already submitted scores
            judge_scores = EventScore.objects.filter(
                heat=heat,
                judge=request.user
            ).exists()
            
            if judge_scores:
                return Response({
                    'error': 'You have already submitted scores for this heat',
                    'scores_submitted': current_scores,
                    'expected_total': expected_total_scores,
                    'remaining_scores': expected_total_scores - current_scores
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                created_scores = []
                for participant_score in scores_data:
                    registration_id = participant_score['registration_id']
                    if registration_id not in heat_participants:
                        return Response({
                            'error': f'Registration ID {registration_id} not found in heat {heat_id}',
                            'valid_registrations': list(heat_participants)
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    criteria_scores = participant_score['criteria_scores']
                    
                    # Calculate total score based on criteria weights
                    total_score = 0
                    for criterion, score in criteria_scores.items():
                        if criterion == 'Negative Marking':
                            continue
                        weight = criteria[criterion]['weight']
                        max_score = criteria[criterion].get('max_score', 150)
                        # weighted_score = (score * weight * max_score)
                        total_score += score
                    
                    # Apply negative marking if any
                    if sub_event.allow_negative_marking:
                        negative_marks = criteria_scores.get('Negative Marking', 0)
                        total_score -= negative_marks
                    
                    # Create score
                    score = EventScore.objects.create(
                        sub_event=sub_event,
                        event_registration_id=registration_id,
                        heat=heat,
                        criteria_scores=criteria_scores,
                        total_score=total_score,
                        judge=request.user
                    )
                    created_scores.append(score)
                
                # Update counts after creating new scores
                current_scores = EventScore.objects.filter(
                    heat=heat
                ).values('judge', 'event_registration').distinct().count()
                
                # Check if all scores are submitted
                all_scores_submitted = current_scores >= expected_total_scores
                
                response_data = {
                    'message': 'Cultural scores submitted successfully',
                    'heat_id': heat_id,
                    'scores_submitted': current_scores,
                    'expected_total': expected_total_scores,
                    'remaining_scores': expected_total_scores - current_scores,
                    'heat_completed': False,
                    'your_scores_submitted': len(created_scores)
                }
                
                # If all scores are submitted, calculate final results
                if all_scores_submitted:
                    final_scores = EventScore.objects.filter(
                        heat=heat
                    ).values(
                        'event_registration'
                    ).annotate(
                        total_final_score=Sum('total_score')
                    ).order_by('-total_final_score')
                    
                    if final_scores:
                        # Get winner and runner-up details
                        winner_data = final_scores[0]
                        runner_up_data = final_scores[1] if len(final_scores) > 1 else None
                        
                        # Update positions and AURA points
                        for score in final_scores:
                            registration_id = score['event_registration']
                            registration = EventRegistration.objects.get(id=registration_id)
                            
                            # Determine position and AURA points
                            if score == winner_data:
                                position = 1
                                aura_points = sub_event.aura_points_winner
                            elif score == runner_up_data:
                                position = 2
                                aura_points = sub_event.aura_points_runner
                            else:
                                position = None
                                aura_points = 0
                            
                            # Update scores and positions
                            if position:
                                EventScore.objects.filter(
                                    heat=heat,
                                    event_registration_id=registration_id
                                ).update(position=position, aura_points=aura_points)
                                
                                HeatParticipant.objects.filter(
                                    heat=heat,
                                    registration_id=registration_id
                                ).update(position=position)
                                
                                # Update department score
                                dept_score, _ = DepartmentScore.objects.get_or_create(
                                    department=registration.department,
                                    year=registration.year,
                                    division=registration.division,
                                    sub_event=sub_event,
                                    defaults={
                                        'total_score': score['total_final_score'],
                                        'aura_points': aura_points
                                    }
                                )
                                if not _:
                                    dept_score.total_score = score['total_final_score']
                                    dept_score.aura_points = aura_points
                                    dept_score.save()
                        
                        # Update heat status
                        heat.status = 'COMPLETED'
                        heat.save()
                        
                        # Add final results to response
                        response_data.update({
                            'heat_completed': True,
                            'final_results': {
                                'winner': {
                                    'registration_id': winner_data['event_registration'],
                                    'total_score': winner_data['total_final_score'],
                                    'aura_points': sub_event.aura_points_winner
                                },
                                'runner_up': {
                                    'registration_id': runner_up_data['event_registration'],
                                    'total_score': runner_up_data['total_final_score'],
                                    'aura_points': sub_event.aura_points_runner
                                } if runner_up_data else None
                            }
                        })
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'error': str(e),
                'detail': 'An error occurred while submitting scores'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def finalize_results(self, request, pk=None):
        """Finalize results and assign AURA points"""
        sub_event = self.get_object()
        
        try:
            with transaction.atomic():
                # Get all scores for this sub_event
                scores = EventScore.objects.filter(
                    sub_event=sub_event
                ).values('event_registration').annotate(
                    avg_score=Avg('total_score')
                ).order_by('-avg_score')
                
                # Handle joint winners
                winners = []
                runners_up = []
                top_score = scores[0]['avg_score'] if scores else 0
                
                for score in scores:
                    if score['avg_score'] == top_score:
                        winners.append(score['event_registration'])
                    elif not runners_up and score['avg_score'] < top_score:
                        runners_up.append(score['event_registration'])
                    elif runners_up and score['avg_score'] == scores[len(winners)]['avg_score']:
                        runners_up.append(score['event_registration'])
                    else:
                        break
                
                # Assign AURA points
                winner_points = sub_event.aura_points_winner
                runner_points = sub_event.aura_points_runner
                
                # Adjust points for joint winners
                if len(winners) > 1 and sub_event.allow_joint_winners:
                    winner_points = (winner_points + runner_points) // 2
                
                # Update scores with final positions and AURA points
                for reg_id in winners:
                    EventScore.objects.filter(
                        sub_event=sub_event,
                        event_registration_id=reg_id
                    ).update(
                        position=1,
                        aura_points=winner_points
                    )
                
                for reg_id in runners_up:
                    EventScore.objects.filter(
                        sub_event=sub_event,
                        event_registration_id=reg_id
                    ).update(
                        position=2,
                        aura_points=runner_points
                    )
                
                return Response({
                    'message': 'Results finalized successfully',
                    'winners': winners,
                    'runners_up': runners_up
                })
                
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

# Additional API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def event_statistics(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    sub_events = event.sub_events.all()
    
    statistics = {
        'total_registrations': EventRegistration.objects.filter(sub_event__event=event).count(),
        'sub_events': [],
        'department_wise': {},
        'year_wise': {}
    }
    
    for sub_event in sub_events:
        registrations = EventRegistration.objects.filter(sub_event=sub_event)
        statistics['sub_events'].append({
            'name': sub_event.name,
            'total_participants': registrations.count(),
            'stage_wise': registrations.values('current_stage').annotate(count=Count('id')),
            'average_score': EventScore.objects.filter(sub_event=sub_event).aggregate(Avg('total_score'))
        })
        
        # Department and year wise statistics
        dept_stats = registrations.values('department').annotate(count=Count('id'))
        year_stats = registrations.values('year').annotate(count=Count('id'))
        
        for stat in dept_stats:
            dept = stat['department']
            if dept not in statistics['department_wise']:
                statistics['department_wise'][dept] = 0
            statistics['department_wise'][dept] += stat['count']
        
        for stat in year_stats:
            year = stat['year']
            if year not in statistics['year_wise']:
                statistics['year_wise'][year] = 0
            statistics['year_wise'][year] += stat['count']
    
    return Response(statistics)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_draws(request, sub_event_slug):
    if request.user.user_type not in ['ADMIN', 'COUNCIL']:
        return Response(
            {'error': 'Unauthorized to generate draws'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    sub_event = get_object_or_404(SubEvent, slug=sub_event_slug)
    stage = request.data.get('stage')
    
    if stage not in dict(SubEvent.EVENT_STAGES).keys():
        return Response(
            {'error': 'Invalid stage'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get eligible registrations for the stage
    registrations = EventRegistration.objects.filter(
        sub_event=sub_event,
        current_stage=stage,
        status='APPROVED'
    )
    
    # Generate random draws
    import random
    registrations_list = list(registrations)
    random.shuffle(registrations_list)
    
    draws = []
    for i in range(0, len(registrations_list), 2):
        if i + 1 < len(registrations_list):
            draw = EventDraw.objects.create(
                sub_event=sub_event,
                stage=stage,
                team1=registrations_list[i],
                team2=registrations_list[i + 1],
                schedule=request.data.get('schedule'),
                venue=request.data.get('venue')
            )
            draws.append(draw)
        else:
            # Handle bye
            EventScore.objects.create(
                sub_event=sub_event,
                registration=registrations_list[i],
                stage=stage,
                is_bye=True,
                judge=request.user,
                updated_by=request.user,
                criteria_scores={},
                total_score=0
            )
    
    serializer = EventDrawSerializer(draws, many=True)
    return Response(serializer.data)

class ScoreboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def department_scoreboard(self, request):
        """Get comprehensive scoreboard with department/year/division breakdowns"""
        from django.db.models import Sum
        
        # Get filter parameters
        department = request.query_params.get('department')
        year = request.query_params.get('year')
        division = request.query_params.get('division')
        event = request.query_params.get('event')
        
        # Base queryset
        scores = DepartmentScore.objects.all()
        
        # Apply filters
        if department:
            scores = scores.filter(department=department)
        if year:
            scores = scores.filter(year=year)
        if division:
            scores = scores.filter(division=division)
        if event:
            scores = scores.filter(sub_event__event_id=event)
            
        # Get total scores
        total_scores = scores.values(
            'department', 'year', 'division'
        ).annotate(
            total_score=Sum('total_score')
        ).order_by('-total_score')
        
        # Get detailed breakdown by sub_event
        detailed_scores = scores.values(
            'department', 'year', 'division',
            'sub_event__name', 'total_score'
        )
        
        # Structure the response
        response = {
            'overall_rankings': total_scores,
            'detailed_scores': detailed_scores,
            'department_wise': self._get_department_rankings(scores),
            'year_wise': self._get_year_rankings(scores),
            'division_wise': self._get_division_rankings(scores)
        }
        
        return Response(response)
    
    def _get_department_rankings(self, scores):
        return scores.values('department').annotate(
            total_score=Sum('total_score')
        ).order_by('-total_score')
    
    def _get_year_rankings(self, scores):
        return scores.values('year').annotate(
            total_score=Sum('total_score')
        ).order_by('-total_score')
    
    def _get_division_rankings(self, scores):
        return scores.values('division').annotate(
            total_score=Sum('total_score')
        ).order_by('-total_score')

    @action(detail=False, methods=['get'])
    def live_updates(self, request):
        """Get recent score updates"""
        recent_scores = DepartmentScore.objects.order_by(
            '-updated_at'
        )[:10].select_related('sub_event')
        
        return Response([{
            'department': score.department,
            'year': score.year,
            'division': score.division,
            'sub_event': score.sub_event.name,
            'total_score': score.total_score,
            'updated_at': score.updated_at
        } for score in recent_scores])
        
    @action(detail=False, methods=['get'])
    def complete_scoreboard(self, request):
        """Get complete scoreboard with all details"""
        try:
            # Get all scores
            scores = DepartmentScore.objects.all().select_related('sub_event', 'sub_event__event')
            
            # Get summary statistics
            summary = {
                'total_departments': scores.values('department').distinct().count(),
                'total_sub_events': scores.values('sub_event').distinct().count(),
                'total_points_awarded': scores.aggregate(
                    total=Coalesce(Sum('total_score'), Decimal('0.00'))
                )['total']
            }
            
            # Get unique class groups (department-year-division combinations)
            class_groups = scores.values(
                'department', 'year', 'division'
            ).distinct().order_by('department', 'year', 'division')
            
            # Get all sub-events
            sub_events = scores.values(
                'sub_event__id',
                'sub_event__name',
                'sub_event__event__name'
            ).distinct()
            
            # Build scores matrix
            sub_event_scores = {}
            class_totals = {}
            
            # Initialize class totals
            for group in class_groups:
                key = f"{group['year']}_{group['department']}_{group['division']}"
                class_totals[key] = Decimal('0.00')
            
            # Calculate scores and totals
            for score in scores:
                class_key = f"{score.year}_{score.department}_{score.division}"
                sub_event_key = score.sub_event.id
                
                # Initialize sub_event dict if not exists
                if sub_event_key not in sub_event_scores:
                    sub_event_scores[sub_event_key] = {
                        'name': score.sub_event.name,
                        'event_name': score.sub_event.event.name,
                        'scores': {}
                    }
                
                # Add score to matrix
                sub_event_scores[sub_event_key]['scores'][class_key] = score.total_score
                
                # Update class total
                class_totals[class_key] += score.total_score
            
            # Calculate department rankings
            department_rankings = []
            for dept in scores.values('department').distinct():
                dept_total = scores.filter(
                    department=dept['department']
                ).aggregate(
                    total=Coalesce(Sum('total_score'), Decimal('0.00'))
                )['total']
                
                department_rankings.append({
                    'department': dept['department'],
                    'total_points': dept_total,
                    'rank': None  # Will be set after sorting
                })
            
            # Sort and assign ranks
            department_rankings.sort(key=lambda x: x['total_points'], reverse=True)
            for i, dept in enumerate(department_rankings, 1):
                dept['rank'] = i
            
            # Format response
            response_data = {
                'summary': summary,
                'sub_event_scores': [
                    {
                        'id': sub_event_id,
                        'name': data['name'],
                        'event_name': data['event_name'],
                        'scores': {
                            class_key: {
                                'score': score,
                                'department': class_key.split('_')[1],
                                'year': class_key.split('_')[0],
                                'division': class_key.split('_')[2]
                            }
                            for class_key, score in data['scores'].items()
                        }
                    }
                    for sub_event_id, data in sub_event_scores.items()
                ],
                'class_totals': [
                    {
                        'department': class_key.split('_')[1],
                        'year': class_key.split('_')[0],
                        'division': class_key.split('_')[2],
                        'total_score': total
                    }
                    for class_key, total in class_totals.items()
                ],
                'department_rankings': department_rankings
            }
            
            return Response(response_data)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=500
            )
    
    
    @action(detail=False, methods=['GET'])
    def overall_scoreboard(self, request):
        """Get complete scoreboard with all breakdowns"""
        try:
            # Get query parameters for filtering
            event_id = request.query_params.get('event')
            department = request.query_params.get('department')
            year = request.query_params.get('year')
            division = request.query_params.get('division')

            # Base queryset
            scores = DepartmentScore.objects.all()

            # Apply filters
            if event_id:
                scores = scores.filter(sub_event__event_id=event_id)
            if department:
                scores = scores.filter(department=department)
            if year:
                scores = scores.filter(year=year)
            if division:
                scores = scores.filter(division=division)

            # Get summary statistics
            summary = {
                'total_score': scores.aggregate(Sum('total_score'))['total_score__sum'] or 0,
                'total_departments': scores.values('department').distinct().count(),
                'total_sub_events': scores.values('sub_event').distinct().count()
            }

            # Get department-wise totals
            department_totals = scores.values('department').annotate(
                total_score=Sum('total_score'),
                sub_events_participated=Count('sub_event', distinct=True)
            ).order_by('-total_score')

            # Get year-wise totals
            year_totals = scores.values('year').annotate(
                total_score=Sum('total_score')
            ).order_by('-total_score')

            # Get division-wise totals
            division_totals = scores.values('division').annotate(
                total_score=Sum('total_score')
            ).order_by('-total_score')

            # Get detailed sub-event scores
            sub_event_scores = {}
            for score in scores:
                key = f"{score.year}_{score.department}_{score.division}"
                if score.sub_event_id not in sub_event_scores:
                    sub_event_scores[score.sub_event_id] = {}
                sub_event_scores[score.sub_event_id][key] = score.total_score

            return Response({
                'summary': summary,
                'department_rankings': department_totals,
                'year_rankings': year_totals,
                'division_rankings': division_totals,
                'sub_event_scores': sub_event_scores
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'])
    def department_scores(self, request):
        """Get scores for a specific department"""
        department = request.query_params.get('department')
        if not department:
            return Response({'error': 'Department parameter is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        scores = DepartmentScore.objects.filter(department=department)
        
        return Response({
            'total_score': scores.aggregate(Sum('total_score'))['total_score__sum'] or 0,
            'sub_event_scores': list(scores.values(
                'sub_event__name', 'total_score', 'year', 'division'
            ))
        })

    @action(detail=False, methods=['GET'])
    def class_scores(self, request):
        """Get scores for a specific class (department-year-division combination)"""
        department = request.query_params.get('department')
        year = request.query_params.get('year')
        division = request.query_params.get('division')

        if not all([department, year, division]):
            return Response(
                {'error': 'Department, year, and division parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        scores = DepartmentScore.objects.filter(
            department=department,
            year=year,
            division=division
        )

        return Response({
            'total_score': scores.aggregate(Sum('total_score'))['total_score__sum'] or 0,
            'sub_event_scores': list(scores.values(
                'sub_event__name', 'total_score'
            ))
        })

    @action(detail=False, methods=['GET'])
    def sub_event_scores(self, request):
        """Get all scores for a specific sub-event"""
        sub_event_id = request.query_params.get('sub_event')
        if not sub_event_id:
            return Response(
                {'error': 'Sub-event parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        scores = DepartmentScore.objects.filter(sub_event_id=sub_event_id)
        
        return Response({
            'sub_event_details': SubEvent.objects.filter(id=sub_event_id).values().first(),
            'scores': list(scores.values(
                'department', 'year', 'division', 'total_score'
            ).order_by('-total_score'))
        })

    @action(detail=False, methods=['get'])
    def overall_summary(self, request):
        """Get overall summary statistics"""
        scores = DepartmentScore.objects.all()
        
        return Response({
            'total_departments': scores.values('department').distinct().count(),
            'total_sub_events': scores.values('sub_event').distinct().count(),
            'total_points': scores.aggregate(
                total=Coalesce(
                    Sum('total_score'), 
                    0,
                    output_field=IntegerField()
                )
            )['total']
        })

    @action(detail=False, methods=['get'])
    def department_rankings(self, request):
        """Get department-wise rankings"""
        department = request.query_params.get('department')
        year = request.query_params.get('year')
        division = request.query_params.get('division')
        
        scores = DepartmentScore.objects.all()
        
        # Apply filters
        if department:
            scores = scores.filter(department=department)
        if year:
            scores = scores.filter(year=year)
        if division:
            scores = scores.filter(division=division)
            
        # Get department totals
        rankings = scores.values(
            'department', 'year', 'division'
        ).annotate(
            total_score=Sum('total_score'),
            event_count=Count('sub_event', distinct=True)
        ).order_by('-total_score')
        
        return Response(rankings)

    @action(detail=False, methods=['get'])
    def subevent_scores(self, request):
        """Get detailed sub-event wise scores"""
        scores = DepartmentScore.objects.all()
        sub_events = SubEvent.objects.all().order_by('name')
        
        # Get all unique class groups
        class_groups = scores.values(
            'year', 'department', 'division'
        ).distinct().order_by('department', 'year', 'division')
        
        # Build scores matrix
        scores_matrix = {}
        for score in scores:
            key = f"{score.year}_{score.department}_{score.division}"
            if score.sub_event_id not in scores_matrix:
                scores_matrix[score.sub_event_id] = {}
            scores_matrix[score.sub_event_id][key] = float(score.total_score)
        
        # Calculate totals for each group
        group_totals = {}
        for group in class_groups:
            key = f"{group['year']}_{group['department']}_{group['division']}"
            total = 0
            for sub_event_id in scores_matrix:
                total += scores_matrix[sub_event_id].get(key, 0)
            group_totals[key] = total
        
        response_data = {
            'sub_events': [{
                'id': sub_event.id,
                'name': sub_event.name,
                'scores': scores_matrix.get(sub_event.id, {})
            } for sub_event in sub_events],
            'class_groups': [{
                'year': group['year'],
                'department': group['department'],
                'division': group['division'],
                'total_score': group_totals.get(
                    f"{group['year']}_{group['department']}_{group['division']}", 0
                )
            } for group in class_groups]
        }
        
        return Response(response_data)

    @action(detail=False, methods=['get'])
    def filters(self, request):
        """Get available filter options"""
        scores = DepartmentScore.objects.all()
        
        return Response({
            'departments': scores.values_list('department', flat=True).distinct(),
            'years': scores.values_list('year', flat=True).distinct(),
            'divisions': scores.values_list('division', flat=True).distinct(),
            'sub_events': SubEvent.objects.values('id', 'name', 'event__name')
        })

    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Get comprehensive leaderboard with multiple groupings"""
        scores = DepartmentScore.objects.all()
        
        # Department-wise totals
        department_totals = scores.values(
            'department'
        ).annotate(
            total_score=Sum('total_score')
        ).order_by('-total_score')
        
        # Year-wise totals
        year_totals = scores.values(
            'year'
        ).annotate(
            total_score=Sum('total_score')
        ).order_by('-total_score')
        
        # Division-wise totals
        division_totals = scores.values(
            'division'
        ).annotate(
            total_score=Sum('total_score')
        ).order_by('-total_score')
        
        # Combined class-wise totals
        class_totals = scores.values(
            'department', 'year', 'division'
        ).annotate(
            total_score=Sum('total_score'),
            event_count=Count('sub_event', distinct=True)
        ).order_by('-total_score')
        
        return Response({
            'department_rankings': department_totals,
            'year_rankings': year_totals,
            'division_rankings': division_totals,
            'class_rankings': class_totals
        })
        
    @action(detail=False, methods=['GET'])
    def matrix_scoreboard(self, request):
        """Get scoreboard in matrix format with sub-events as rows and class groups as columns"""
        try:
            event_id = request.query_params.get('event')
            
            # Get all sub-events for the event
            sub_events = SubEvent.objects.filter(event_id=event_id).order_by('name')
            
            # Get all unique class combinations
            scores = DepartmentScore.objects.all()
            if event_id:
                scores = scores.filter(sub_event__event_id=event_id)
            
            class_groups = scores.values(
                'department', 'year', 'division'
            ).distinct().order_by('department', 'year', 'division')

            # Create class group labels
            columns = []
            for group in class_groups:
                column_label = f"{group['year']} {group['department']} {group['division']}"
                columns.append({
                    'id': f"{group['year']}_{group['department']}_{group['division']}",
                    'label': column_label,
                    'department': group['department'],
                    'year': group['year'],
                    'division': group['division']
                })

            # Create score matrix
            matrix_data = []
            for sub_event in sub_events:
                row = {
                    'sub_event_id': sub_event.id,
                    'sub_event_name': sub_event.name,
                    'scores': {}
                }
                
                # Get scores for this sub-event
                sub_event_scores = scores.filter(sub_event=sub_event)
                for group in class_groups:
                    key = f"{group['year']}_{group['department']}_{group['division']}"
                    score = sub_event_scores.filter(
                        department=group['department'],
                        year=group['year'],
                        division=group['division']
                    ).first()
                    row['scores'][key] = score.total_score if score else 0
                
                matrix_data.append(row)

            # Calculate column totals
            column_totals = {}
            for group in class_groups:
                key = f"{group['year']}_{group['department']}_{group['division']}"
                total = scores.filter(
                    department=group['department'],
                    year=group['year'],
                    division=group['division']
                ).aggregate(total=Sum('total_score'))['total'] or 0
                column_totals[key] = total

            # Get top 3 class groups
            sorted_totals = sorted(
                column_totals.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            top_performers = [
                {
                    'rank': idx + 1,
                    'class_group': key,
                    'total_points': total
                } for idx, (key, total) in enumerate(sorted_totals)
            ]

            return Response({
                'columns': columns,  # Class groups (TE COMPS A, etc.)
                'matrix_data': matrix_data,  # Sub-event wise scores
                'column_totals': column_totals,  # Total scores for each class
                'top_performers': top_performers,  # Top 3 class groups
                'event_id': event_id,
                'total_sub_events': len(sub_events),
                'total_class_groups': len(class_groups)
            })

        except Exception as e:
            return Response({'error': str(e)}, status=400)
        
class FacultyViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(user_type='FACULTY')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def assigned_subevents(self, request, **kwargs):
        """Get all sub-events assigned to this faculty"""
        faculty = self.get_object()
        assignments = SubEventFaculty.objects.filter(
            faculty=faculty,
            is_active=True
        ).select_related(
            'sub_event',
            'sub_event__event'
        )
        
        subevent_data = []
        for assignment in assignments:
            sub_event = assignment.sub_event
            subevent_data.append({
                'id': sub_event.id,
                'name': sub_event.name,
                'event': {
                    'id': sub_event.event.id,
                    'name': sub_event.event.name
                },
                'venue': sub_event.venue,
                'assigned_at': assignment.assigned_at,
                'schedule': sub_event.schedule
            })
        
        return Response(subevent_data)

    @action(detail=False, methods=['get'])
    def my_subevents(self, request):
        """Get all sub-events assigned to the logged-in faculty"""
        if request.user.user_type != 'FACULTY':
            return Response(
                {"error": "Only faculty members can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
    
        assignments = SubEventFaculty.objects.filter(
            faculty=request.user,
            is_active=True
        ).select_related(
            'sub_event',
            'sub_event__event'
        )
        
        subevent_data = []
        for assignment in assignments:
            sub_event = assignment.sub_event
            subevent_data.append({
                'id': sub_event.id,
                'name': sub_event.name,
                'event': {
                    'id': sub_event.event.id,
                    'name': sub_event.event.name
                },
                'venue': sub_event.venue,
                'assigned_at': assignment.assigned_at,
                'schedule': sub_event.schedule
            })
        
        return Response(subevent_data)

class EventCriteriaViewSet(viewsets.ModelViewSet):
    queryset = EventCriteria.objects.all()
    serializer_class = EventCriteriaSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def get_criteria_by_event(self, request):
        """Get scoring criteria for a specific event"""
        event_name = request.query_params.get('event_name')
        if not event_name:
            return Response(
                {"error": "event_name parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            criteria = EventCriteria.objects.get(
                name=event_name,
                is_active=True
            )
            return Response(criteria.criteria)
        except EventCriteria.DoesNotExist:
            return Response(
                {"error": f"No criteria found for event: {event_name}"},
                status=status.HTTP_404_NOT_FOUND
            )

class ScoreboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overall_standings(self, request):
        """Get overall department standings"""
        # Get query parameters
        year = request.query_params.get('year')
        division = request.query_params.get('division')
        event_id = request.query_params.get('event')
        
        # Base query
        scores = DepartmentScore.objects.all()
        
        # Apply filters
        if year:
            scores = scores.filter(year=year)
        if division:
            scores = scores.filter(division=division)
        if event_id:
            scores = scores.filter(sub_event__event_id=event_id)
            
        # Get department-wise totals
        department_scores = scores.values(
            'department'
        ).annotate(
            total_aura_points=Sum('aura_points'),
            total_events=Count('sub_event', distinct=True)
        ).order_by('-total_aura_points')
        
        # Get detailed breakdown
        detailed_scores = scores.values(
            'department', 'year', 'division'
        ).annotate(
            total_aura_points=Sum('aura_points'),
            total_events=Count('sub_event', distinct=True)
        ).order_by('-total_aura_points')
        
        return Response({
            'department_standings': department_scores,
            'detailed_standings': detailed_scores
        })
    
    @action(detail=False, methods=['get'])
    def department_statistics(self, request):
        """Get detailed statistics for a department"""
        department = request.query_params.get('department')
        if not department:
            return Response(
                {"error": "Department parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Get all scores for the department
        scores = DepartmentScore.objects.filter(department=department)
        
        # Event type breakdown
        event_type_stats = scores.values(
            'sub_event__category'
        ).annotate(
            total_points=Sum('aura_points'),
            event_count=Count('sub_event', distinct=True)
        )
        
        # Top performing events
        top_events = scores.values(
            'sub_event__name',
            'sub_event__category'
        ).annotate(
            points=Sum('aura_points')
        ).order_by('-points')[:5]
        
        # Year/Division performance
        year_division_stats = scores.values(
            'year', 'division'
        ).annotate(
            total_points=Sum('aura_points'),
            event_count=Count('sub_event', distinct=True)
        ).order_by('-total_points')
        
        return Response({
            'department': department,
            'total_points': scores.aggregate(total=Sum('aura_points'))['total'] or 0,
            'event_type_breakdown': event_type_stats,
            'top_events': top_events,
            'year_division_performance': year_division_stats
        })
    
    @action(detail=False, methods=['get'])
    def event_leaderboard(self, request):
        """Get leaderboard for a specific event"""
        event_id = request.query_params.get('event')
        if not event_id:
            return Response(
                {"error": "Event parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        scores = DepartmentScore.objects.filter(
            sub_event__event_id=event_id
        )
        
        # Department standings
        department_standings = scores.values(
            'department'
        ).annotate(
            total_points=Sum('aura_points'),
            sub_events_participated=Count('sub_event', distinct=True)
        ).order_by('-total_points')
        
        # Sub-event breakdown
        sub_event_breakdown = scores.values(
            'sub_event__name',
            'department'
        ).annotate(
            points=Sum('aura_points')
        ).order_by('sub_event__name', '-points')
        
        return Response({
            'department_standings': department_standings,
            'sub_event_breakdown': sub_event_breakdown
        })

class SubEventFacultyViewSet(viewsets.ModelViewSet):
    queryset = SubEventFaculty.objects.all()
    serializer_class = SubEventFacultySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'FACULTY':
            return self.queryset.filter(faculty=self.request.user, is_active=True)
        return self.queryset
    
    @action(detail=False, methods=['get'])
    def my_assignments(self, request):
        """Get faculty's judging assignments"""
        if request.user.user_type != 'FACULTY':
            return Response(
                {"error": "Only faculty members can access assignments"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        assignments = self.queryset.filter(
            faculty=request.user,
            # is_active=True,
            # sub_event__current_stage__in=['ONGOING', 'SCORING']
        )
        
        return Response(self.serializer_class(assignments, many=True).data)
    
    @action(detail=True, methods=['post'])
    def submit_scores(self, request, pk=None):
        """Submit scores for assigned sub-event"""
        faculty_assignment = self.get_object()
        
        if request.user != faculty_assignment.faculty:
            return Response(
                {"error": "Unauthorized to submit scores"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        scores_data = request.data.get('scores', [])
        
        try:
            with transaction.atomic():
                for score_data in scores_data:
                    registration_id = score_data.pop('registration_id')
                    EventScore.objects.create(
                        sub_event=faculty_assignment.sub_event,
                        event_registration_id=registration_id,
                        judge=request.user,
                        criteria_scores=score_data.get('criteria_scores', {}),
                        remarks=score_data.get('remarks', '')
                    )
                
                return Response({'message': 'Scores submitted successfully'})
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def overall_standings(request):
    try:
        # Get all sub events
        sub_events = SubEvent.objects.filter(
            event__category='SPORTS'  # Adjust if needed for different categories
        )
        
        # Define all departments
        all_departments = [
            'FE-A', 'FE-B', 'FE-C', 'FE-D', 'FE-E', 'FE-F',
            'SE-COMPS-A', 'SE-COMPS-B', 'SE-AIML-C', 'SE-AIML-D', 'SE-IT', 'SE-DE',
            'TE-COMPS-A', 'TE-COMPS-B', 'TE-AIML-C', 'TE-AIML-D', 'TE-IT', 'TE-DE',
            'BE-COMPS-A', 'BE-COMPS-B', 'BE-AIML-C', 'BE-AIML-D', 'BE-IT', 'BE-DE'
        ]

        # Initialize response structure
        sub_event_scores = []
        
        # Get scores for each sub event
        for sub_event in sub_events:
            scores_dict = {}
            
            # Get scores for this sub event
            department_scores = DepartmentScore.objects.filter(
                sub_event=sub_event
            ).select_related('department')
            
            # Populate scores for each department
            for department in all_departments:
                dept_score = department_scores.filter(
                    department=department
                ).first()
                
                scores_dict[department] = {
                    'score': dept_score.total_score if dept_score else None,
                    'aura_points': dept_score.aura_points if dept_score else None
                }
            
            sub_event_scores.append({
                'name': sub_event.name,
                'scores': scores_dict
            })

        # Calculate class totals
        class_totals = []
        for department in all_departments:
            total_score = DepartmentScore.objects.filter(
                department=department
            ).aggregate(
                total_score=Sum('total_score')
            )['total_score'] or 0
            
            class_totals.append({
                'department': department,
                'total_score': total_score
            })

        # Calculate department rankings
        department_rankings = []
        sorted_totals = sorted(
            class_totals,
            key=lambda x: x['total_score'],
            reverse=True
        )
        
        for rank, dept_data in enumerate(sorted_totals, 1):
            department_rankings.append({
                'rank': rank,
                'department': dept_data['department'],
                'total_points': dept_data['total_score']
            })

        return Response({
            'sub_event_scores': sub_event_scores,
            'class_totals': class_totals,
            'department_rankings': department_rankings
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_registrations(request):
    """Export all sub-event registrations to CSV"""
    try:
        # Get all sub events
        sub_events = SubEvent.objects.all().order_by('name')
        
        # Create the HttpResponse object with CSV header
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="event_registrations_{timestamp}.csv"'
        
        # Create CSV writer
        writer = csv.writer(response)
        
        # Define common headers
        headers = [
            'Registration No.',
            'Registration Date',
            'Participant/Team Name',
            'Department',
            'Year',
            'Division',
            'Contact Number',
            'Email',
            'Team Members',  # For team events
            'Team Members Departments',  # For team events
            'Team Members Years',  # For team events
            'Team Members Divisions',  # For team events
            'Status',
            'Current Stage',
            'Last Updated'
        ]
        
        # Write data for each sub-event
        for sub_event in sub_events:
            # Add sub-event header
            writer.writerow([])  # Empty row for spacing
            writer.writerow([f'Sub Event: {sub_event.name}'])
            writer.writerow([f'Event Type: {sub_event.participation_type}'])
            writer.writerow([f'Category: {sub_event.category}'])
            writer.writerow([])  # Empty row for spacing
            
            # Write headers
            writer.writerow(headers)
            
            # Get registrations for this sub-event, handling duplicates
            registrations = EventRegistration.objects.filter(
                sub_event=sub_event
            ).values(
                'team_leader_id',
                'team_name'
            ).annotate(
                latest_id=Max('id')  # Get the latest registration for each team/individual
            ).values_list('latest_id', flat=True)
            
            # Get full registration objects
            registrations = EventRegistration.objects.filter(
                id__in=registrations
            ).order_by('registration_number')
            
            # Write registration data
            for reg in registrations:
                team_members = reg.team_members.all()
                
                # Format team members data
                if sub_event.participation_type == 'GROUP':
                    team_members_names = ', '.join([
                        f"{member.first_name} {member.last_name}" 
                        for member in team_members
                    ])
                    team_members_depts = ', '.join([
                        str(member.department) for member in team_members
                    ])
                    team_members_years = ', '.join([
                        str(member.year_of_study) for member in team_members
                    ])
                    team_members_divisions = ', '.join([
                        str(member.division) for member in team_members
                    ])
                else:
                    # For individual events, use participant's data
                    participant = team_members.first()
                    team_members_names = f"{participant.first_name} {participant.last_name}" if participant else ''
                    team_members_depts = participant.department if participant else ''
                    team_members_years = participant.year_of_study if participant else ''
                    team_members_divisions = participant.division if participant else ''
                
                row = [
                    reg.registration_number,
                    # reg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    reg.team_name if sub_event.participation_type == 'GROUP' else team_members_names,
                    reg.department,
                    reg.year,
                    reg.division,
                    # reg.team_leader.phone,
                    # reg.team_leader.email,
                    team_members_names,
                    team_members_depts,
                    team_members_years,
                    team_members_divisions,
                    reg.status,
                    reg.current_stage,
                    reg.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                ]
                writer.writerow(row)
        
        return response
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )