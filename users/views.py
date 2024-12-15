

# Create your views here.
# # users/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
# from rest_framework.response import Response
# from .models import User, CouncilMember, Faculty

# users/views.py
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from .utils import generate_otp
from rest_framework import status, permissions
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .models import User, CouncilMember, Faculty
from .serializers import UserSerializer, CouncilMemberSerializer, FacultySerializer

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
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    email = request.data.get('email')
    
    # Check if email exists in database
    try:
        user = User.objects.get(email=email)
        if user.is_active:
            return Response({
                'error': 'User already registered with this email'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate and send OTP
        generate_otp(user)
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
