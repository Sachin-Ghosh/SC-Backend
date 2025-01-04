from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db import models 
from django.shortcuts import get_object_or_404
from .models import Event, SubEvent, EventRegistration, EventScore, EventDraw , Organization , SubEventImage, EventHeat , SubmissionFile , User
from .serializers import EventSerializer, SubEventSerializer, EventRegistrationSerializer, EventScoreSerializer, EventDrawSerializer , OrganizationSerializer , SubEventImageSerializer, EventHeatSerializer
from rest_framework import viewsets, status     
from django.db.models import Q, Count, Avg, Sum
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.decorators import action
from rest_framework.routers import DefaultRouter
from rest_framework.views import APIView
import random
from django.conf import settings
from django.contrib.auth.models import User

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

# SubEvent ViewSet
class SubEventViewSet(viewsets.ModelViewSet):
    queryset = SubEvent.objects.all()
    serializer_class = SubEventSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    
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
            self._send_registration_email(registration)
        except Exception as e:
            print(f"Failed to send confirmation email: {str(e)}")

        return Response(serializer.data, status=201)

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