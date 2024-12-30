from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db import models 
from django.shortcuts import get_object_or_404
from .models import Event, SubEvent, EventRegistration, EventScore, EventDraw , Organization , SubEventImage
from .serializers import EventSerializer, SubEventSerializer, EventRegistrationSerializer, EventScoreSerializer, EventDrawSerializer , OrganizationSerializer , SubEventImageSerializer
from rest_framework import viewsets, status     
from django.db.models import Q, Count, Avg
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.decorators import action
from rest_framework.routers import DefaultRouter
from rest_framework.views import APIView

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
def event_statistics(request):
    total_events = Event.objects.count()
    total_participants = EventRegistration.objects.values('participant').distinct().count()
    department_wise_participation = EventRegistration.objects.values('department').annotate(
        count=models.Count('id')
    )
    
    return Response({
        'total_events': total_events,
        'total_participants': total_participants,
        'department_wise_participation': department_wise_participation
    })
# Add these views to your existing views.py file

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sub_event_detail(request, event_slug, sub_event_slug):
    sub_event = get_object_or_404(SubEvent, event__slug=event_slug, slug=sub_event_slug)
    serializer = SubEventSerializer(sub_event)
    return Response(serializer.data)

@api_view(['PUT'])
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

# SubEvent ViewSet
class SubEventViewSet(viewsets.ModelViewSet):
    queryset = SubEvent.objects.all()
    serializer_class = SubEventSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    
    @action(detail=True, methods=['post'])
    def add_images(self, request, slug=None):
        sub_event = self.get_object()
        images_data = request.FILES.getlist('images')
        captions = request.POST.getlist('captions')
        
        created_images = []
        for image, caption in zip(images_data, captions):
            sub_event_image = SubEventImage.objects.create(
                image=image,
                caption=caption
            )
            created_images.append(sub_event_image)
        
        sub_event.images.add(*created_images)
        return Response({'message': 'Images added successfully'})
    
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

class EventRegistrationViewSet(viewsets.ModelViewSet):
    queryset = EventRegistration.objects.all()
    serializer_class = EventRegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type in ['ADMIN', 'COUNCIL']:
            return EventRegistration.objects.all()
        return EventRegistration.objects.filter(
            Q(team_leader=self.request.user) | 
            Q(team_members=self.request.user)
        ).distinct()

    def create(self, request, *args, **kwargs):
        sub_event = get_object_or_404(SubEvent, id=request.data.get('sub_event'))
        
        # Check if registration is open
        if timezone.now() > sub_event.registration_deadline:
            return Response(
                {'error': 'Registration deadline has passed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if maximum participants limit reached
        if EventRegistration.objects.filter(sub_event=sub_event).count() >= sub_event.max_participants:
            return Response(
                {'error': 'Maximum participants limit reached'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(
            data=request.data,
            context={'sub_event': sub_event, 'team_leader': request.user}
        )
        serializer.is_valid(raise_exception=True)
        registration = serializer.save(team_leader=request.user)
        
        # Send confirmation email
        self._send_registration_confirmation(registration)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _send_registration_confirmation(self, registration):
        subject = f'Registration Confirmation - {registration.sub_event.name}'
        message = render_to_string('events/registration_confirmation_email.html', {
            'registration': registration,
            'event': registration.sub_event.event,
            'sub_event': registration.sub_event,
        })
        recipient_list = [registration.team_leader.email]
        recipient_list.extend([member.email for member in registration.team_members.all()])
        
        send_mail(subject, message, None, recipient_list)

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
        if self.request.user.user_type in ['ADMIN', 'COUNCIL', 'FACULTY']:
            return EventScore.objects.all()
        return EventScore.objects.filter(
            registration__team_leader=self.request.user
        )

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