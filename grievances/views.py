from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Count
from .models import Grievance, MediaFile
from .serializers import GrievanceSerializer, MediaFileSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def grievance_list(request):
    grievances = Grievance.objects.all()
    if request.user.user_type == 'STUDENT':
        grievances = grievances.filter(submitted_by=request.user)
    serializer = GrievanceSerializer(grievances, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_grievance(request):
    serializer = GrievanceSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(submitted_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def grievance_detail(request, pk):
    grievance = get_object_or_404(Grievance, pk=pk)
    if request.user.user_type == 'STUDENT' and grievance.submitted_by != request.user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    serializer = GrievanceSerializer(grievance)
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_grievance(request, pk):
    grievance = get_object_or_404(Grievance, pk=pk)
    if request.user.user_type == 'STUDENT' and grievance.submitted_by != request.user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    serializer = GrievanceSerializer(grievance, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_grievance(request, pk):
    grievance = get_object_or_404(Grievance, pk=pk)
    if request.user.user_type not in ['ADMIN', 'COUNCIL']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    grievance.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_grievance(request, pk):
    if request.user.user_type not in ['ADMIN', 'COUNCIL']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    grievance = get_object_or_404(Grievance, pk=pk)
    assigned_to = request.data.get('assigned_to')
    if assigned_to:
        grievance.assigned_to_id = assigned_to
        grievance.status = 'INVESTIGATING'
        grievance.save()
        serializer = GrievanceSerializer(grievance)
        return Response(serializer.data)
    return Response({'error': 'Assigned user required'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_grievance(request, pk):
    if request.user.user_type not in ['ADMIN', 'COUNCIL']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    grievance = get_object_or_404(Grievance, pk=pk)
    resolution = request.data.get('resolution')
    if resolution:
        grievance.resolution = resolution
        grievance.status = 'RESOLVED'
        grievance.resolved_date = timezone.now()
        grievance.save()
        serializer = GrievanceSerializer(grievance)
        return Response(serializer.data)
    return Response({'error': 'Resolution required'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_grievance(request, pk):
    if request.user.user_type not in ['ADMIN', 'COUNCIL']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    grievance = get_object_or_404(Grievance, pk=pk)
    reason = request.data.get('reason')
    if reason:
        grievance.resolution = reason
        grievance.status = 'REJECTED'
        grievance.resolved_date = timezone.now()
        grievance.save()
        serializer = GrievanceSerializer(grievance)
        return Response(serializer.data)
    return Response({'error': 'Rejection reason required'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def add_evidence(request, pk):
    grievance = get_object_or_404(Grievance, pk=pk)
    if request.user != grievance.submitted_by and request.user.user_type not in ['ADMIN', 'COUNCIL']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    files = request.FILES.getlist('files')
    if not files:
        return Response({'error': 'No files provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    media_files = []
    for file in files:
        media_data = {
            'file': file,
            'file_type': request.data.get('file_type', 'DOCUMENT'),
            'description': request.data.get('description'),
            'uploaded_by': request.user.id,
            'size': file.size
        }
        serializer = MediaFileSerializer(data=media_data)
        if serializer.is_valid():
            media_file = serializer.save()
            media_files.append(media_file)
    
    grievance.evidence.add(*media_files)
    return Response({'message': f'{len(media_files)} files uploaded successfully'})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_evidence(request, pk, evidence_id):
    grievance = get_object_or_404(Grievance, pk=pk)
    if request.user != grievance.submitted_by and request.user.user_type not in ['ADMIN', 'COUNCIL']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    media_file = get_object_or_404(MediaFile, pk=evidence_id)
    grievance.evidence.remove(media_file)
    return Response({'message': 'Evidence removed successfully'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_grievances(request):
    grievances = Grievance.objects.filter(submitted_by=request.user)
    serializer = GrievanceSerializer(grievances, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def assigned_grievances(request):
    if request.user.user_type not in ['ADMIN', 'COUNCIL']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    grievances = Grievance.objects.filter(assigned_to=request.user)
    serializer = GrievanceSerializer(grievances, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def grievance_statistics(request):
    if request.user.user_type not in ['ADMIN', 'COUNCIL']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    stats = {
        'total_grievances': Grievance.objects.count(),
        'pending_grievances': Grievance.objects.filter(status='PENDING').count(),
        'resolved_grievances': Grievance.objects.filter(status='RESOLVED').count(),
        'rejected_grievances': Grievance.objects.filter(status='REJECTED').count(),
        'by_type': Grievance.objects.values('grievance_type').annotate(count=Count('id')),
        'by_event': Grievance.objects.values('event__name').annotate(count=Count('id'))
    }
    return Response(stats)

# Media File Management Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_media(request):
    serializer = MediaFileSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(uploaded_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def media_detail(request, pk):
    media = get_object_or_404(MediaFile, pk=pk)
    if not media.is_public and request.user != media.uploaded_by:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    serializer = MediaFileSerializer(media)
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_media(request, pk):
    media = get_object_or_404(MediaFile, pk=pk)
    if request.user != media.uploaded_by and request.user.user_type not in ['ADMIN', 'COUNCIL']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    media.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)