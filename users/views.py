# users/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from .utils import generate_otp
from rest_framework import status, permissions
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .models import User, CouncilMember, Faculty
from .serializers import UserSerializer, CouncilMemberSerializer, FacultySerializer
from django.conf import settings
from django.core.mail import send_mail
import os
import random
import string
from django.db.models import Count
from django.contrib.auth import logout
from django.db.models import Q
from datetime import datetime, timedelta

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.all()
        user_type = self.request.query_params.get('user_type', None)
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        return queryset

class CouncilMemberViewSet(viewsets.ModelViewSet):
    queryset = CouncilMember.objects.all()
    serializer_class = CouncilMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

class FacultyViewSet(viewsets.ModelViewSet):
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer
    permission_classes = [permissions.IsAuthenticated]

def send_otp_email(email, otp):
    subject = 'Your OTP for Registration'
    message = f'Your OTP is: {otp}. Valid for 10 minutes.'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    
    send_mail(subject, message, from_email, recipient_list)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    email = request.data.get('email')
    year_of_study = request.data.get('year_of_study')
    
    # Validate email domain except for FE students
    if year_of_study != 'FE' and not email.endswith('@college.edu'):  # Replace with your college domain
        return Response({
            'error': 'Must use college email address'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        if user.is_active:
            return Response({
                'error': 'User already registered with this email'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate and send OTP
        otp = ''.join(random.choices(string.digits, k=6))
        user.otp = otp
        user.otp_valid_until = timezone.now() + timezone.timedelta(minutes=10)
        user.save()
        
        send_otp_email(email, otp)
        
        return Response({
            'message': 'OTP sent to your email'
        })
        
    except User.DoesNotExist:
        return Response({
            'error': 'Email not found in our database'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@parser_classes([MultiPartParser, FormParser])
def verify_and_complete_registration(request):
    email = request.data.get('email')
    otp = request.data.get('otp')
    password = request.data.get('password')
    id_card = request.FILES.get('id_card_document')
    
    try:
        user = User.objects.get(email=email)
        
        # Verify OTP
        if not user.otp or user.otp != otp or timezone.now() > user.otp_valid_until:
            return Response({
                'error': 'Invalid or expired OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check ID card for students and council members
        if user.user_type in ['STUDENT', 'COUNCIL']:
            if not id_card:
                return Response({
                    'error': 'ID card document is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            user.id_card_document = id_card
        
        # Complete registration
        user.set_password(password)
        user.is_active = True
        user.otp = None
        user.otp_valid_until = None
        user.save()
        
        return Response({
            'message': 'Registration completed successfully'
        })
        
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_user(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'error': 'Please provide both email and password'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(email=email, password=password)
    
    if user:
        # Check if council member's term has ended
        if user.user_type == 'COUNCIL':
            try:
                council_member = user.councilmember
                if timezone.now().date() > council_member.term_end:
                    user.user_type = 'STUDENT'
                    user.save()
                    council_member.delete()
            except CouncilMember.DoesNotExist:
                pass
        
        serializer = UserSerializer(user)
        return Response({
            'message': 'Login successful',
            'user': serializer.data
        })
    return Response({
        'error': 'Invalid credentials'
    }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    try:
        serializer = UserSerializer(request.user)
        return Response({
            'profile': serializer.data
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    try:
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'profile': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def council_members_list(request):
    try:
        council_members = CouncilMember.objects.all()
        serializer = CouncilMemberSerializer(council_members, many=True)
        return Response({
            'council_members': serializer.data
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def faculty_list(request):
    try:
        faculty = Faculty.objects.all()
        serializer = FacultySerializer(faculty, many=True)
        return Response({
            'faculty': serializer.data
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def promote_to_council(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        if user.user_type != 'STUDENT':
            return Response({
                'error': 'Only students can be promoted to council'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update user type
        user.user_type = 'COUNCIL'
        user.save()
        
        # Create council member entry
        council_data = request.data
        council_data['user'] = user.id
        serializer = CouncilMemberSerializer(data=council_data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Successfully promoted to council member',
                'data': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def view_id_card(request, user_id):
    if not request.user.user_type in ['ADMIN', 'COUNCIL', 'FACULTY']:
        return Response({
            'error': 'Unauthorized to view ID cards'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        if not user.id_card_document:
            return Response({
                'error': 'No ID card document found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'id_card_url': request.build_absolute_uri(user.id_card_document.url)
        })
    
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_user(request):
    logout(request)
    return Response({'message': 'Successfully logged out'})

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def request_password_reset(request):
    email = request.data.get('email')
    try:
        user = User.objects.get(email=email)
        otp = generate_otp()
        user.otp = otp
        user.otp_valid_until = timezone.now() + timezone.timedelta(minutes=10)
        user.save()
        send_otp_email(email, otp)
        return Response({'message': 'Password reset OTP sent to email'})
    except User.DoesNotExist:
        return Response({'error': 'Email not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    email = request.data.get('email')
    otp = request.data.get('otp')
    new_password = request.data.get('new_password')
    
    try:
        user = User.objects.get(email=email)
        if user.otp != otp or timezone.now() > user.otp_valid_until:
            return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.otp = None
        user.otp_valid_until = None
        user.save()
        return Response({'message': 'Password reset successful'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    
    if not user.check_password(old_password):
        return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(new_password)
    user.save()
    return Response({'message': 'Password changed successfully'})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_id_card(request):
    if 'id_card_document' not in request.FILES:
        return Response({'error': 'No ID card document provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    user.id_card_document = request.FILES['id_card_document']
    try:
        user.full_clean()
        user.save()
        return Response({'message': 'ID card uploaded successfully'})
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def users_by_department(request, department):
    users = User.objects.filter(department=department)
    serializer = UserSerializer(users, many=True)
    return Response({'users': serializer.data})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def users_by_year(request, year):
    users = User.objects.filter(year_of_study=year)
    serializer = UserSerializer(users, many=True)
    return Response({'users': serializer.data})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def users_by_division(request, division):
    users = User.objects.filter(division=division)
    serializer = UserSerializer(users, many=True)
    return Response({'users': serializer.data})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def demote_from_council(request, user_id):
    if not request.user.user_type == 'ADMIN':
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        if user.user_type != 'COUNCIL':
            return Response({'error': 'User is not a council member'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.user_type = 'STUDENT'
        user.save()
        
        try:
            council_member = user.councilmember
            council_member.delete()
        except CouncilMember.DoesNotExist:
            pass
        
        return Response({'message': 'Successfully demoted from council'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def active_council_members(request):
    current_date = timezone.now().date()
    active_members = CouncilMember.objects.filter(term_end__gte=current_date)
    serializer = CouncilMemberSerializer(active_members, many=True)
    return Response({'active_council_members': serializer.data})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def expired_council_members(request):
    current_date = timezone.now().date()
    expired_members = CouncilMember.objects.filter(term_end__lt=current_date)
    serializer = CouncilMemberSerializer(expired_members, many=True)
    return Response({'expired_council_members': serializer.data})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def faculty_by_department(request, department):
    faculty = Faculty.objects.filter(user__department=department)
    serializer = FacultySerializer(faculty, many=True)
    return Response({'faculty': serializer.data})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def faculty_by_subject(request, subject):
    faculty = Faculty.objects.filter(subjects__icontains=subject)
    serializer = FacultySerializer(faculty, many=True)
    return Response({'faculty': serializer.data})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_id_card(request, user_id):
    if not request.user.user_type in ['ADMIN', 'FACULTY']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        if not user.id_card_document:
            return Response({'error': 'No ID card document found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Add verification logic here
        return Response({'message': 'ID card verified successfully'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def users_summary(request):
    if not request.user.user_type in ['ADMIN', 'FACULTY']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    summary = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'students': User.objects.filter(user_type='STUDENT').count(),
        'faculty': User.objects.filter(user_type='FACULTY').count(),
        'council_members': User.objects.filter(user_type='COUNCIL').count(),
    }
    return Response(summary)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def department_distribution(request):
    if not request.user.user_type in ['ADMIN', 'FACULTY']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    distribution = User.objects.values('department').annotate(count=Count('id'))
    return Response(distribution)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def year_distribution(request):
    if not request.user.user_type in ['ADMIN', 'FACULTY']:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    distribution = User.objects.values('year_of_study').annotate(count=Count('id'))
    return Response(distribution)
