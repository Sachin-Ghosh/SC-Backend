from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Achievement
from .serializers import AchievementSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def achievement_list(request):
    achievements = Achievement.objects.all()
    if request.user.user_type == 'STUDENT':
        achievements = achievements.filter(achiever=request.user)
    serializer = AchievementSerializer(achievements, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_achievement(request):
    serializer = AchievementSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(achiever=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def achievement_detail(request, slug):
    achievement = get_object_or_404(Achievement, slug=slug)
    if request.user.user_type == 'STUDENT' and achievement.achiever != request.user:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    serializer = AchievementSerializer(achievement)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_achievement(request, slug):
    if request.user.user_type not in ['ADMIN', 'COUNCIL', 'FACULTY']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    achievement = get_object_or_404(Achievement, slug=slug)
    if achievement.is_verified:
        return Response({'error': 'Achievement already verified'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    achievement.is_verified = True
    achievement.verified_by = request.user
    achievement.save()
    
    serializer = AchievementSerializer(achievement)
    return Response({
        'message': 'Achievement verified successfully',
        'achievement': serializer.data
    })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_achievements(request):
    achievements = Achievement.objects.filter(achiever=request.user)
    serializer = AchievementSerializer(achievements, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_verification(request):
    if request.user.user_type not in ['ADMIN', 'COUNCIL', 'FACULTY']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    achievements = Achievement.objects.filter(is_verified=False)
    serializer = AchievementSerializer(achievements, many=True)
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_achievement(request, slug):
    achievement = get_object_or_404(Achievement, slug=slug)
    
    # Only allow achiever or admin to update
    if request.user != achievement.achiever and request.user.user_type != 'ADMIN':
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    # If already verified, only admin can update
    if achievement.is_verified and request.user.user_type != 'ADMIN':
        return Response({'error': 'Cannot update verified achievement'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    serializer = AchievementSerializer(achievement, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_achievement(request, slug):
    achievement = get_object_or_404(Achievement, slug=slug)
    
    # Only allow achiever or admin to delete
    if request.user != achievement.achiever and request.user.user_type != 'ADMIN':
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    # If already verified, only admin can delete
    if achievement.is_verified and request.user.user_type != 'ADMIN':
        return Response({'error': 'Cannot delete verified achievement'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    achievement.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)