from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db import models 
from django.shortcuts import get_object_or_404
from .models import Event, SubEvent, EventRegistration, EventScore, EventDraw , Organization , SubEventImage, EventHeat , SubmissionFile , User, SubEventFaculty, DepartmentScore, HeatParticipant
from .serializers import EventSerializer, SubEventSerializer, EventRegistrationSerializer, EventScoreSerializer, EventDrawSerializer , OrganizationSerializer , SubEventImageSerializer, EventHeatSerializer, SubEventFacultySerializer, HeatParticipantSerializer
from rest_framework import viewsets, status     
from django.db.models import Q, Count, Avg, Sum
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
        queryset = SubEvent.objects.all()
        
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
                
        return queryset.select_related('event').prefetch_related(
            'sub_heads',
            'images'
        )

    def retrieve(self, request, *args, **kwargs):
        """Get sub-event details by ID with optional filters"""
        try:
            sub_event = self.get_object()
            
            # Get query parameters for filtering
            stage = request.query_params.get('stage')
            status = request.query_params.get('status')
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
            
            if status:
                registrations = registrations.filter(status=status)
                heats = heats.filter(status=status)
            
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
                    # for stage in sub_event.stages
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
                    heats.order_by('-created_at')[:5],  # Changed from created_at to id
                    many=True
                ).data,
                'recent_scores': EventScoreSerializer(
                    scores.order_by('-updated_at')[:5],  # Changed from created_at to updated_at
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

    @action(detail=True, methods=['post'])
    def generate_heats(self, request, slug=None):
        """Generate heats for the next round"""
        sub_event = self.get_object()
        round_number = request.data.get('round_number', sub_event.current_round)
        
        # Get qualified participants for this round
        if round_number == 1:
            participants = EventRegistration.objects.filter(
                sub_event=sub_event,
                status='APPROVED'
            )
        else:
            # Get participants who qualified from previous round
            participants = EventRegistration.objects.filter(
                sub_event=sub_event,
                scores__round_number=round_number-1,
                scores__qualified_for_next=True
            ).distinct()
        
        # Shuffle participants
        participants = list(participants)
        random.shuffle(participants)
        
        # Create heats
        heats_needed = (len(participants) + sub_event.participants_per_group - 1) // sub_event.participants_per_group
        
        heats = []
        for heat_number in range(1, heats_needed + 1):
            heat = EventHeat.objects.create(
                sub_event=sub_event,
                round_number=round_number,
                heat_number=heat_number
            )
            
            # Assign participants to this heat
            start_idx = (heat_number - 1) * sub_event.participants_per_group
            end_idx = min(start_idx + sub_event.participants_per_group, len(participants))
            heat_participants = participants[start_idx:end_idx]
            heat.participants.set(heat_participants)
            heats.append(heat)
        
        serializer = EventHeatSerializer(heats, many=True)
        return Response(serializer.data)

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
    def round_participants(self, request, slug=None):
        """Get participants for each round"""
        sub_event = self.get_object()
        round_number = request.query_params.get('round', sub_event.current_round)

        heats = EventHeat.objects.filter(
            sub_event=sub_event,
            round_number=round_number
        ).prefetch_related(
            'participants__team_leader',
            'participants__team_members'
        )

        heat_data = []
        for heat in heats:
            participants = []
            for registration in heat.participants.all():
                participants.append({
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
                    'scores': registration.scores.filter(
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

    @action(detail=True, methods=['post'])
    def submit_scores(self, request, pk=None):
        """Submit scores for participants"""
        sub_event = self.get_object()
        scores_data = request.data.get('scores', [])
        
        results = []
        for score_data in scores_data:
            try:
                score = EventScore.objects.create(
                    sub_event=sub_event,
                    event_registration_id=score_data['registration_id'],
                    judge=request.user,
                    total_score=score_data['total_score'],
                    criteria_scores=score_data.get('criteria_scores', {}),
                    remarks=score_data.get('remarks')
                )
                results.append(EventScoreSerializer(score).data)
            except Exception as e:
                results.append({'error': str(e)})
        
        return Response(results)

    @action(detail=True, methods=['get'])
    def registrations(self, request, pk=None):
        """Get all registrations for this sub-event"""
        sub_event = self.get_object()
        registrations = EventRegistration.objects.filter(sub_event=sub_event)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            registrations = registrations.filter(status=status_filter)
            
        return Response(EventRegistrationSerializer(registrations, many=True).data)

    @action(detail=True, methods=['get'])
    def scores(self, request, pk=None):
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
    @action(detail=True, methods=['post'])
    def create_heat(self, request, pk=None):
        """Create a new heat for the sub-event"""
        sub_event = self.get_object()
        
        try:
            heat = EventHeat.objects.create(
                sub_event=sub_event,
                name=request.data.get('name'),
                stage=request.data.get('stage'),
                round_number=request.data.get('round_number'),
                schedule=request.data.get('schedule'),
                venue=request.data.get('venue'),
                max_participants=request.data.get('max_participants', 0),
                status='PENDING'
            )
            
            return Response(EventHeatSerializer(heat).data)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'])
    def assign_participants_to_heat(self, request, pk=None):
        """Assign participants to a specific heat"""
        heat_id = request.data.get('heat_id')
        registration_ids = request.data.get('registration_ids', [])
        
        if not heat_id or not registration_ids:
            return Response({
                'error': 'heat_id and registration_ids are required'
            }, status=400)
            
        try:
            heat = EventHeat.objects.get(id=heat_id, sub_event_id=pk)
            
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

    @action(detail=True, methods=['get'])
    def get_heats(self, request, pk=None):
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

    @action(detail=True, methods=['get'])
    def get_available_participants(self, request, pk=None):
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

class EventHeatViewSet(viewsets.ModelViewSet):
    queryset = EventHeat.objects.all()
    serializer_class = EventHeatSerializer
    
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

    @action(detail=True, methods=['post'])
    def remove_participants(self, request, pk=None):
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

    @action(detail=True, methods=['get'])
    def get_participants(self, request, pk=None):
        """Get all participants in this heat"""
        heat = self.get_object()
        participants = HeatParticipant.objects.filter(heat=heat)
        
        return Response(HeatParticipantSerializer(participants, many=True).data)

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

    # def create(self, request, *args, **kwargs):
    #     sub_event = get_object_or_404(SubEvent, id=request.data.get('sub_event'))
        
    #     # Validate registration window
    #     if not self._validate_registration_window(sub_event):
    #         return Response({"error": "Registration is not open"}, status=400)
        
        
    #     # Validate gender restrictions
    #     if not self._validate_gender_participation(request.user, sub_event):
    #         return Response(
    #             {"error": f"This event is restricted to {sub_event.get_gender_participation_display()} participants"}, 
    #             status=400
    #         )

    #     # Prepare registration data
    #     registration_data = request.data.copy()
        
    #     if sub_event.participation_type == 'SOLO':
    #         # Solo event: only one participant, no team leader or team name
    #         registration_data.pop('team_leader', None)
    #         registration_data.pop('team_name', None)
    #         registration_data.pop('team_members', None)  # Will add current user later
    #     else:
    #         # Team event: requires team name and optionally team members
    #         if not registration_data.get('team_name'):
    #             return Response({"error": "Team name is required"}, status=400)
    #         registration_data['team_leader'] = request.user.id

    #     # Create registration
    #     serializer = self.get_serializer(data=registration_data)
    #     serializer.is_valid(raise_exception=True)
    #     registration = serializer.save()

    #     # Add participants
    #     if sub_event.participation_type == 'SOLO':
    #         registration.team_members.add(request.user)
    #     else:
    #         # Add team leader and members
    #         registration.team_members.add(request.user)
    #         team_members = registration_data.get('team_members', [])
    #         if team_members:
    #             registration.team_members.add(*team_members)

    #     # Send confirmation email
    #     try:
    #         self._send_registration_email(registration)
    #     except Exception as e:
    #         print(f"Failed to send confirmation email: {str(e)}")

    #     return Response(serializer.data, status=201)

    def create(self, request, *args, **kwargs):
        """Create registration with current user as team leader"""
        try:
            # Get the sub_event and validate it exists
            sub_event = get_object_or_404(SubEvent, id=request.data.get('sub_event'))
            
            # Create registration data
            registration_data = {
                'sub_event_id': sub_event.id,
                'team_leader_id': request.user.id,  # Set team leader ID explicitly
                'department': request.data.get('department'),
                'year': request.data.get('year'),
                'division': request.data.get('division'),
                'team_name': request.data.get('team_name'),
                'current_stage': 'REGISTRATION',
                'status': 'PENDING'
            }
            
            # Create registration
            registration = EventRegistration.objects.create(**registration_data)
            
            # Handle team members based on event type
            if sub_event.participation_type == 'SOLO':
                # For solo events, don't add any team members
                pass
            elif sub_event.participation_type == 'TEAM':
                # For team events, add team members if provided
                team_members = request.data.get('team_members', [])
                if team_members:
                    registration.team_members.set(team_members)
            
            # Refresh and serialize
            registration.refresh_from_db()
            serializer = self.get_serializer(registration)
            
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
    def _validate_registration_window(self, sub_event):
        current_time = timezone.now()
        if not sub_event.registration_start_time or not sub_event.registration_end_time:
            return False
        return sub_event.registration_start_time <= current_time <= sub_event.registration_end_time

    def _send_registration_email(self, registration):
        context = {
            'registration': registration,
            'event': registration.sub_event.event,
            'sub_event': registration.sub_event,
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
            return Response([], status=status.HTTP_200_OK)

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
    @action(detail=False, methods=['post'])
    def submit_score(self, request):
        """
        Submit scores for a participant/team
        """
        sub_event_id = request.data.get('sub_event')
        registration_id = request.data.get('registration')
        
        # Validate permissions
        if not self._can_submit_score(request.user, sub_event_id):
            return Response(
                {"error": "You are not authorized to submit scores for this event"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get or create score object
        score_data = {
            'sub_event_id': sub_event_id,
            'event_registration_id': registration_id,
            'judge': request.user,
            'stage': request.data.get('stage'),
            'round_number': request.data.get('round_number'),
            'heat_id': request.data.get('heat'),
            'total_score': request.data.get('total_score'),
            'criteria_scores': request.data.get('criteria_scores', {}),
            'position': request.data.get('position'),
            'remarks': request.data.get('remarks'),
            'qualified_for_next': request.data.get('qualified_for_next', False)
        }

        serializer = self.get_serializer(data=score_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
            total_points=Sum('points')
        ).order_by('-total_points')
        
        # Get detailed breakdown by sub_event
        detailed_scores = scores.values(
            'department', 'year', 'division',
            'sub_event__name', 'points'
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
            total_points=Sum('points')
        ).order_by('-total_points')
    
    def _get_year_rankings(self, scores):
        return scores.values('year').annotate(
            total_points=Sum('points')
        ).order_by('-total_points')
    
    def _get_division_rankings(self, scores):
        return scores.values('division').annotate(
            total_points=Sum('points')
        ).order_by('-total_points')

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
            'points': score.points,
            'updated_at': score.updated_at
        } for score in recent_scores])
        
        
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
                'total_points': scores.aggregate(Sum('points'))['points__sum'] or 0,
                'total_departments': scores.values('department').distinct().count(),
                'total_sub_events': scores.values('sub_event').distinct().count()
            }

            # Get department-wise totals
            department_totals = scores.values('department').annotate(
                total_points=Sum('points'),
                sub_events_participated=Count('sub_event', distinct=True)
            ).order_by('-total_points')

            # Get year-wise totals
            year_totals = scores.values('year').annotate(
                total_points=Sum('points')
            ).order_by('-total_points')

            # Get division-wise totals
            division_totals = scores.values('division').annotate(
                total_points=Sum('points')
            ).order_by('-total_points')

            # Get detailed sub-event scores
            sub_event_scores = {}
            for score in scores:
                key = f"{score.year}_{score.department}_{score.division}"
                if score.sub_event_id not in sub_event_scores:
                    sub_event_scores[score.sub_event_id] = {}
                sub_event_scores[score.sub_event_id][key] = score.points

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
            'total_points': scores.aggregate(Sum('points'))['points__sum'] or 0,
            'sub_event_scores': list(scores.values(
                'sub_event__name', 'points', 'year', 'division'
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
            'total_points': scores.aggregate(Sum('points'))['points__sum'] or 0,
            'sub_event_scores': list(scores.values(
                'sub_event__name', 'points'
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
                'department', 'year', 'division', 'points'
            ).order_by('-points'))
        })

    @action(detail=False, methods=['GET'])
    def leaderboard(self, request):
        """Get top performing departments/classes"""
        scores = DepartmentScore.objects.all()
        
        # Get top departments
        top_departments = scores.values('department').annotate(
            total_points=Sum('points')
        ).order_by('-total_points')[:5]

        # Get top classes
        top_classes = scores.values(
            'department', 'year', 'division'
        ).annotate(
            total_points=Sum('points')
        ).order_by('-total_points')[:5]

        return Response({
            'top_departments': top_departments,
            'top_classes': top_classes
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
                    row['scores'][key] = score.points if score else 0
                
                matrix_data.append(row)

            # Calculate column totals
            column_totals = {}
            for group in class_groups:
                key = f"{group['year']}_{group['department']}_{group['division']}"
                total = scores.filter(
                    department=group['department'],
                    year=group['year'],
                    division=group['division']
                ).aggregate(total=Sum('points'))['total'] or 0
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