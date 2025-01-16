# users/views.py
from django.forms import ValidationError
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from django.utils import timezone
from urllib.parse import unquote
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from .utils import generate_otp
from rest_framework import status, permissions
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from .models import User, CouncilMember, Faculty
from .serializers import UserSerializer, CouncilMemberSerializer, FacultySerializer
from django.conf import settings
from django.core.mail import send_mail
import os
from django.template.loader import render_to_string
from django.utils import timezone
from .utils import generate_name_from_email
import random
import string
from django.db.models import Count
from django.contrib.auth import logout
from django.db.models import Q
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from PIL import Image
import pytesseract
import re

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

def send_registration_email(user, otp):
    """Send registration confirmation and OTP email"""
    context = {
        'user': user,
        'otp': otp,
        'valid_minutes': 10  # OTP validity in minutes
    }
    
    subject = 'Welcome to Student Council Website - Verify Your Email'
    html_message = render_to_string('emails/registration_welcome.html', context)
    plain_message = render_to_string('emails/registration_welcome.txt', context)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email]
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False
    
def verify_college_id(image_file):
    try:
        image = Image.open(image_file)
        text = pytesseract.image_to_string(image)
        college_name_pattern = r"Universal College of Engineering"  # For time being Just using the college name later we can add more steps        
        has_college_name = bool(re.search(college_name_pattern, text, re.IGNORECASE))
        
        # print("Extracted Text:", text)
        # print("College Name Found:", has_college_name)
        
        if has_college_name:
            return True, "Valid college ID card"
        else:
            return False, "Invalid college ID card"
            
    except Exception as e:
        return False, f"Error processing image: {str(e)}"
# @api_view(['POST'])
# @permission_classes([permissions.AllowAny])
# def register_user(request):
#     email = request.data.get('email')
#     year_of_study = request.data.get('year_of_study')
    
#     # Validate email domain except for FE students
#     if year_of_study != 'FE' and not email.endswith('@universal.edu.in'):  # Replace with your college domain
#         return Response({
#             'error': 'Must use college email address'
#         }, status=status.HTTP_400_BAD_REQUEST)
    
#     try:
#         user = User.objects.get(email=email)
#         if user.is_active:
#             return Response({
#                 'error': 'User already registered with this email'
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         # Generate and send OTP
#         otp = ''.join(random.choices(string.digits, k=6))
#         user.otp = otp
#         user.otp_valid_until = timezone.now() + timezone.timedelta(minutes=10)
#         user.save()
        
#         send_otp_email(email, otp)
        
#         return Response({
#             'message': 'OTP sent to your email'
#         })
        
#     except User.DoesNotExist:
#         return Response({
#             'error': 'Email not found in our database'
#         }, status=status.HTTP_404_NOT_FOUND)

# @api_view(['POST'])
# @permission_classes([permissions.AllowAny])
# @parser_classes([MultiPartParser, FormParser])
# def verify_and_complete_registration(request):
#     email = request.data.get('email')
#     otp = request.data.get('otp')
#     password = request.data.get('password')
#     id_card = request.FILES.get('id_card_document')
    
#     try:
#         user = User.objects.get(email=email)
        
#         # Verify OTP
#         if not user.otp or user.otp != otp or timezone.now() > user.otp_valid_until:
#             return Response({
#                 'error': 'Invalid or expired OTP'
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         # Check ID card for students and council members
#         if user.user_type in ['STUDENT', 'COUNCIL']:
#             if not id_card:
#                 return Response({
#                     'error': 'ID card document is required'
#                 }, status=status.HTTP_400_BAD_REQUEST)
#             user.id_card_document = id_card
        
#         # Complete registration
#         user.set_password(password)
#         user.is_active = True
#         user.otp = None
#         user.otp_valid_until = None
#         user.save()
        
#         return Response({
#             'message': 'Registration completed successfully'
#         })
        
#     except User.DoesNotExist:
#         return Response({
#             'error': 'User not found'
#         }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        user_type = request.data.get('user_type')
        department = request.data.get('department')
        
        if not all([email, password, user_type, department]):
            return Response({
                'error': 'Email, password, user type and department are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate email domain
        if not email.endswith('@universal.edu.in'):
            return Response({
                'error': 'Must use college email address (@universal.edu.in)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'User already exists with this email'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Generate first_name and last_name from email
        first_name, last_name = generate_name_from_email(email)
        
        
        # Create user and generate OTP
        try:
            user = User.objects.create(
                email=email,
                username=email.split('@')[0],
                first_name=first_name,
                last_name=last_name,
                user_type=user_type,
                department=department,
                is_active=False
            )
            user.set_password(password)
            
            otp = ''.join(random.choices(string.digits, k=6))
            user.otp = otp
            user.otp_valid_until = timezone.now() + timezone.timedelta(minutes=10)
            user.save()
            
            # Verify template existence
            template_path = os.path.join(settings.BASE_DIR, 'sc_backend', 'templates', 'emails', 'registration_welcome.html')
            if not os.path.exists(template_path):
                raise Exception(f"Template not found at: {template_path}")
            
            # Prepare email
            context = {
                'user': user,
                'otp': otp,
                'valid_minutes': 10
            }
            
            try:
                html_message = render_to_string('emails/registration_welcome.html', context)
                plain_message = render_to_string('emails/registration_welcome.txt', context)
                
                # Send email
                send_mail(
                    subject='Welcome to Student Council - Verify Your Email',
                    message=plain_message,
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                return Response({
                    'message': 'Registration successful! Please check your email for OTP',
                    'email': email
                })
                
            except Exception as e:
                user.delete()  # Cleanup if email fails
                return Response({
                    'error': f'Email error: {str(e)}',
                    'template_path': template_path
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'error': f'User creation error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'error': f'Registration error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
       

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp(request):
    email = request.data.get('email')
    otp = request.data.get('otp')
    
    try:
        user = User.objects.get(email=email)
        
        # Verify OTP
        if not user.otp or user.otp != otp:
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check OTP expiration
        if timezone.now() > user.otp_valid_until:
            return Response({
                'error': 'OTP has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Activate user
        user.is_active = True
        user.otp = None
        user.otp_valid_until = None
        
        # Add additional user information
        user.first_name = request.data.get('first_name', '')
        user.last_name = request.data.get('last_name', '')
        user.department = request.data.get('department', '')
        user.phone = request.data.get('phone', '')
        user.profile_picture = request.data.get('profile_picture', '')
        user.bio = request.data.get('bio', '')
        user.gender = request.data.get('gender', '')
        
        if user.user_type == 'STUDENT':
            user.year_of_study = request.data.get('year_of_study', '')
            user.division = request.data.get('division', '')
            user.roll_number = request.data.get('roll_number', '')
            user.id_card_document = request.data.get('id_card_document', '')
            
        
        elif user.user_type == 'FACULTY':
            user.designation = request.data.get('designation', '')
            user.subjects = request.data.get('subjects', [])
            
        elif user.user_type == 'COUNCIL':
            user.year_of_study = request.data.get('year_of_study', '')
            user.division = request.data.get('division', '')
            user.roll_number = request.data.get('roll_number', '')
            user.id_card_document = request.data.get('id_card_document', '')
            user.position = request.data.get('position', '')
            user.term_start = request.data.get('term_start')
            user.term_end = request.data.get('term_end')
        
        user.save()
        
        # Create specific user type instance if needed
        if user.user_type == 'FACULTY':
            Faculty.objects.create(
                user=user,
                designation=user.designation,
                subjects=user.subjects
            )
        elif user.user_type == 'COUNCIL':
            CouncilMember.objects.create(
                user=user,
                position=user.position,
                term_start=user.term_start,
                term_end=user.term_end
            )
        
        serializer = UserSerializer(user)
        return Response({
            'message': 'Registration completed successfully',
            'user': serializer.data
        })
        
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        user.delete()
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_user(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'error': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        
        if not user.is_active:
            return Response({
                'error': 'Please verify your email first'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=user.username, password=password)
        
        if user:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Login successful',
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'user_type': user.user_type,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            })
        else:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except User.DoesNotExist:
        return Response({
            'error': 'No user found with this email'
        }, status=status.HTTP_404_NOT_FOUND)

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

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def resend_otp(request):
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        user = User.objects.get(email=email)
        
        # Check if user is already active
        if user.is_active:
            return Response({
                'error': 'User is already verified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate new OTP
        new_otp = ''.join(random.choices(string.digits, k=6))
        user.otp = new_otp
        user.otp_valid_until = timezone.now() + timezone.timedelta(minutes=10)
        user.save()
        
        # Send new OTP email
        context = {
            'user': user,
            'otp': new_otp,
            'valid_minutes': 10
        }
        
        subject = 'Your New OTP for Student Council Registration'
        html_message = render_to_string('emails/resend_otp.html', context)
        plain_message = render_to_string('emails/resend_otp.txt', context)
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email]
            )
            
            return Response({
                'message': 'New OTP sent successfully',
                'email': email
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to send OTP email: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except User.DoesNotExist:
        return Response({
            'error': 'No user found with this email. Please register first.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        user.delete()
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
    try:
        refresh_token = request.data.get('refresh_token')
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        return Response({
            'message': 'Logged out successfully'
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def request_password_reset(request):
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        user = User.objects.get(email=email)
        
        # Generate password reset token
        reset_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        user.reset_password_token = reset_token
        user.reset_password_token_valid_until = timezone.now() + timezone.timedelta(hours=1)
        user.save()
        
        # Send reset email
        subject = 'Password Reset Request'
        message = f'Your password reset token is: {reset_token}\nValid for 1 hour.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        
        send_mail(subject, message, from_email, recipient_list)
        
        return Response({
            'message': 'Password reset instructions sent to your email'
        })
        
    except User.DoesNotExist:
        return Response({
            'error': 'No user found with this email'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    email = request.data.get('email')
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    if not all([email, token, new_password]):
        return Response({
            'error': 'Email, token and new password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        user = User.objects.get(email=email)
        
        # Verify token
        if not user.reset_password_token or user.reset_password_token != token:
            return Response({
                'error': 'Invalid reset token'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Check token expiration
        if timezone.now() > user.reset_password_token_valid_until:
            return Response({
                'error': 'Reset token has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Reset password
        user.set_password(new_password)
        user.reset_password_token = None
        user.reset_password_token_valid_until = None
        user.save()
        
        return Response({
            'message': 'Password reset successful'
        })
        
    except User.DoesNotExist:
        return Response({
            'error': 'No user found with this email'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    
    if not all([old_password, new_password]):
        return Response({
            'error': 'Old password and new password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    # Verify old password
    if not user.check_password(old_password):
        return Response({
            'error': 'Invalid old password'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    # Set new password
    user.set_password(new_password)
    user.save()
    
    return Response({
        'message': 'Password changed successfully'
    })

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
@permission_classes([permissions.AllowAny])
def verify_id_card(request):
    if 'id_card_document' not in request.FILES:
        return Response({'error': 'No ID card document provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    id_card = request.FILES['id_card_document']
    is_valid, message = verify_college_id(id_card)
    
    return Response({
        'is_valid': is_valid,
        'message': message
    }, status=status.HTTP_200_OK if is_valid else status.HTTP_400_BAD_REQUEST)

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

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_detail(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        serializer = UserSerializer(user)
        
        # Get additional information based on user type
        additional_info = {}
        if user.user_type == 'COUNCIL':
            try:
                council_info = CouncilMemberSerializer(user.councilmember).data
                additional_info['council_info'] = council_info
            except CouncilMember.DoesNotExist:
                pass
                
        elif user.user_type == 'FACULTY':
            try:
                faculty_info = FacultySerializer(user.faculty).data
                additional_info['faculty_info'] = faculty_info
            except Faculty.DoesNotExist:
                pass
        
        response_data = {
            'user': serializer.data,
            'additional_info': additional_info
        }
        
        return Response(response_data)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_detail_by_username(request, username):
    """
    Get user details by username instead of directly calling user_detail
    """
    try:
        user = User.objects.get(username=username)
        serializer = UserSerializer(user)
        
        # Get additional information based on user type
        additional_info = {}
        if user.user_type == 'COUNCIL':
            try:
                council_info = CouncilMemberSerializer(user.councilmember).data
                additional_info['council_info'] = council_info
            except CouncilMember.DoesNotExist:
                pass
                
        elif user.user_type == 'FACULTY':
            try:
                faculty_info = FacultySerializer(user.faculty).data
                additional_info['faculty_info'] = faculty_info
            except Faculty.DoesNotExist:
                pass
        
        response_data = {
            'user': serializer.data,
            'additional_info': additional_info
        }
        
        return Response(response_data)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def council_member_detail(request, member_id):
    try:
        council_member = CouncilMember.objects.get(id=member_id)
        serializer = CouncilMemberSerializer(council_member)
        
        # Get additional statistics and information
        response_data = {
            'council_member': serializer.data,
            'days_remaining': (council_member.term_end - timezone.now().date()).days,
            'is_active': council_member.term_end >= timezone.now().date(),
            'term_duration': (council_member.term_end - council_member.term_start).days,
        }
        
        return Response(response_data)
    except CouncilMember.DoesNotExist:
        return Response(
            {'error': 'Council member not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def council_member_history(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        council_history = CouncilMember.objects.filter(user=user).order_by('-term_start')
        
        if not council_history.exists():
            return Response(
                {'message': 'No council member history found for this user'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CouncilMemberSerializer(council_history, many=True)
        
        # Calculate total service time
        total_days = sum(
            (member.term_end - member.term_start).days 
            for member in council_history
        )
        
        response_data = {
            'user': UserSerializer(user).data,
            'council_history': serializer.data,
            'total_positions': council_history.count(),
            'total_service_days': total_days,
            'positions_held': list(council_history.values_list('position', flat=True).distinct())
        }
        
        return Response(response_data)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def faculty_detail(request, faculty_id):
    try:
        faculty = Faculty.objects.get(id=faculty_id)
        serializer = FacultySerializer(faculty)
        
        # Get additional information
        subjects_list = faculty.subjects.split(',') if faculty.subjects else []
        
        # Get all students under this faculty's department
        department_students = User.objects.filter(
            department=faculty.user.department,
            user_type='STUDENT'
        ).count()
        
        response_data = {
            'faculty': serializer.data,
            'subjects_count': len(subjects_list),
            'subjects_list': subjects_list,
            'department_students': department_students,
            'contact_info': {
                'email': faculty.user.email,
                'phone': faculty.user.phone,
                'office_location': faculty.office_location,
                'office_hours': faculty.office_hours
            }
        }
        
        return Response(response_data)
    except Faculty.DoesNotExist:
        return Response(
            {'error': 'Faculty member not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def faculty_schedule(request, faculty_id):
    try:
        faculty = Faculty.objects.get(id=faculty_id)
        
        # This is a placeholder for faculty schedule
        # You would typically connect this to a schedule/timetable model
        schedule = {
            'office_hours': faculty.office_hours,
            'subjects': faculty.subjects.split(',') if faculty.subjects else [],
            'department': faculty.user.department,
            'availability': {
                'Monday': '9:00 AM - 5:00 PM',
                'Tuesday': '9:00 AM - 5:00 PM',
                'Wednesday': '9:00 AM - 5:00 PM',
                'Thursday': '9:00 AM - 5:00 PM',
                'Friday': '9:00 AM - 5:00 PM'
            }
        }
        
        return Response({
            'faculty': FacultySerializer(faculty).data,
            'schedule': schedule
        })
    except Faculty.DoesNotExist:
        return Response(
            {'error': 'Faculty member not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

def clean_filter_param(param):
    """Clean and standardize filter parameters"""
    if param is None:
        return ''
    return unquote(str(param)).strip()

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def filter_users(request):
    """
    Get users with multiple filter options.
    Example: /api/users/filter/?department=COMPUTER&year=TE&division=A&gender=MALE&user_type=STUDENT
    """
    try:
        users = User.objects.all()

        # Basic Filters
        department = unquote(request.query_params.get('department', ''))
        year = request.query_params.get('year')
        division = request.query_params.get('division')
        gender = request.query_params.get('gender')
        user_type = request.query_params.get('user_type')
        is_active = request.query_params.get('is_active')
        
        # Additional Filters
        search = request.query_params.get('search')
        has_profile_picture = request.query_params.get('has_profile_picture')
        has_id_card = request.query_params.get('has_id_card')
        position = request.query_params.get('position')  # For council members
        designation = request.query_params.get('designation')  # For faculty
        roll_number = request.query_params.get('roll_number')
        
        # Date Filters
        joined_after = request.query_params.get('joined_after')
        joined_before = request.query_params.get('joined_before')

        # Apply filters
        if department:
            users = users.filter(department__iexact=department)
        
        if year:
            users = users.filter(year_of_study=year)
        
        if division:
            users = users.filter(division=division)
        
        if gender:
            users = users.filter(gender=gender)
        
        if user_type:
            users = users.filter(user_type=user_type)
        
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            users = users.filter(is_active=is_active)
        
        if search:
            users = users.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search) |
                Q(roll_number__icontains=search)
            )
        
        if has_profile_picture is not None:
            has_profile_picture = has_profile_picture.lower() == 'true'
            if has_profile_picture:
                users = users.exclude(profile_picture='')
            else:
                users = users.filter(profile_picture='')
        
        if has_id_card is not None:
            has_id_card = has_id_card.lower() == 'true'
            if has_id_card:
                users = users.exclude(id_card_document='')
            else:
                users = users.filter(id_card_document='')
        
        if position and user_type == 'COUNCIL':
            users = users.filter(position=position)
        
        if designation and user_type == 'FACULTY':
            users = users.filter(designation=designation)
        
        if roll_number:
            users = users.filter(roll_number__icontains=roll_number)
        
        if joined_after:
            users = users.filter(date_joined__gte=joined_after)
        
        if joined_before:
            users = users.filter(date_joined__lte=joined_before)

        # Sorting
        sort_by = request.query_params.get('sort_by', 'date_joined')
        sort_order = request.query_params.get('sort_order', 'desc')
        
        if sort_order.lower() == 'asc':
            users = users.order_by(sort_by)
        else:
            users = users.order_by(f'-{sort_by}')

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size

        # Count total before slicing
        total_count = users.count()
        
        # Apply pagination
        users = users[start:end]

        # Serialize data
        serializer = UserSerializer(users, many=True)

        return Response({
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'results': serializer.data,
            'filters_applied': {
                'department': department,
                'year': year,
                'division': division,
                'gender': gender,
                'user_type': user_type,
                'is_active': is_active,
                'has_profile_picture': has_profile_picture,
                'has_id_card': has_id_card,
                'position': position,
                'designation': designation,
                'roll_number': roll_number,
                'joined_after': joined_after,
                'joined_before': joined_before,
                'search': search
            }
        })

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
