from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db import models 
from django.shortcuts import get_object_or_404
from .models import Event, SubEvent, EventRegistration, EventScore
from .serializers import EventSerializer, SubEventSerializer, EventRegistrationSerializer, EventScoreSerializer


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