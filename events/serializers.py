# events/serializers.py
from rest_framework import serializers
from django_summernote.fields import SummernoteTextField
from .models import (
    Organization, Event, SubEvent, SubEventImage, EventRegistration,
    SubmissionFile, EventDraw, EventScore, EventHeat, SubEventFaculty,
    HeatParticipant
)
from users.serializers import UserSerializer

class OrganizationSerializer(serializers.ModelSerializer):
    description = serializers.CharField(style={'base_template': 'textarea.html'})

    class Meta:
        model = Organization
        fields = '__all__'

class SubEventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubEventImage
        fields = '__all__'

class EventSerializer(serializers.ModelSerializer):
    chairpersons = UserSerializer(many=True, read_only=True)
    vice_chairpersons = UserSerializer(many=True, read_only=True)
    event_heads = UserSerializer(many=True, read_only=True)
    collaborating_organizations = OrganizationSerializer(many=True, read_only=True)
    description = serializers.CharField(style={'base_template': 'textarea.html'})
    
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ('slug', 'created_by')

class SubEventFacultySerializer(serializers.ModelSerializer):
    faculty_name = serializers.SerializerMethodField()
    faculty_email = serializers.EmailField(source='faculty.email', read_only=True)
    
    faculty = UserSerializer(read_only=True)  # Add this line


    class Meta:
        model = SubEventFaculty
        fields = ['id', 'faculty', 'faculty_name', 'faculty_email', 'sub_event', 'is_active', 'remarks']
        read_only_fields = ['assigned_at']

    def get_faculty_name(self, obj):
        try:
            return f"{obj.faculty.first_name} {obj.faculty.last_name}".strip()
        except:
            return "Unknown Faculty"

    def get_faculty_email(self, obj):
        try:
            return obj.faculty.email
        except:
            return None

    
class SubEventSerializer(serializers.ModelSerializer):
    images = SubEventImageSerializer(many=True, read_only=True)
    sub_heads = UserSerializer(many=True, read_only=True)
    description = serializers.CharField(style={'base_template': 'textarea.html'})
    short_description = serializers.CharField(style={'base_template': 'textarea.html'})
    prize_pool_description = serializers.CharField(style={'base_template': 'textarea.html'})
    format_description = serializers.CharField(style={'base_template': 'textarea.html'})
    rules = serializers.CharField(style={'base_template': 'textarea.html'})
    faculty_judges = SubEventFacultySerializer(source='subeventfaculty_set',many=True, read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)
    total_participants = serializers.SerializerMethodField()
    total_heats = serializers.SerializerMethodField()
    
    class Meta:
        model = SubEvent
        fields = '__all__'
        read_only_fields = ('slug',)
        
    def get_total_participants(self, obj):
        return obj.eventregistration_set.count()
    
    def get_total_heats(self, obj):
        return obj.eventheat_set.count()

class SubmissionFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionFile
        fields = '__all__'

class EventRegistrationSerializer(serializers.ModelSerializer):
    team_leader = UserSerializer(read_only=True)
    team_members = UserSerializer(many=True, read_only=True)
    team_member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = EventRegistration
        fields = '__all__'
        read_only_fields = ('registration_number', 'status','team_leader')
        
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['team_leader'] = request.user
        return super().create(validated_data)
    
    def validate_team_member_ids(self, value):
        sub_event = self.context['sub_event']
        team_leader = self.context['team_leader']
        
        # Validate team size
        if len(value) + 1 < sub_event.min_team_size:
            raise serializers.ValidationError(f"Minimum team size is {sub_event.min_team_size}")
        if len(value) + 1 > sub_event.max_team_size:
            raise serializers.ValidationError(f"Maximum team size is {sub_event.max_team_size}")
        
        # Validate team members
        from django.contrib.auth import get_user_model
        User = get_user_model()
        team_members = User.objects.filter(id__in=value)
        
        # Check if all members exist
        if len(team_members) != len(value):
            raise serializers.ValidationError("One or more team members not found")
        
        # Check department/year/division restrictions if applicable
        if not sub_event.allow_mixed_department:
            departments = set(member.department for member in team_members)
            if len(departments) > 1 or team_leader.department not in departments:
                raise serializers.ValidationError("All team members must be from the same department")
        
        if not sub_event.allow_mixed_year:
            years = set(member.year_of_study for member in team_members)
            if len(years) > 1 or team_leader.year_of_study not in years:
                raise serializers.ValidationError("All team members must be from the same year")
        
        if not sub_event.allow_mixed_division:
            divisions = set(member.division for member in team_members)
            if len(divisions) > 1 or team_leader.division not in divisions:
                raise serializers.ValidationError("All team members must be from the same division")
        
        return value
    
    def create(self, validated_data):
        team_member_ids = validated_data.pop('team_member_ids', [])
        registration = super().create(validated_data)
        if team_member_ids:
            registration.team_members.set(team_member_ids)
        return registration

class EventDrawSerializer(serializers.ModelSerializer):
    team1_details = EventRegistrationSerializer(source='team1', read_only=True)
    team2_details = EventRegistrationSerializer(source='team2', read_only=True)
    winner_details = EventRegistrationSerializer(source='winner', read_only=True)
    
    class Meta:
        model = EventDraw
        fields = '__all__'

class EventScoreSerializer(serializers.ModelSerializer):
    judge_name = serializers.CharField(source='judge.get_full_name', read_only=True)
    participant_name = serializers.SerializerMethodField()
    sub_event_name = serializers.SerializerMethodField()

    
    class Meta:
        model = EventScore
        fields = '__all__'
        read_only_fields = ('points_awarded',)
        
    def get_judge_name(self, obj):
        return obj.judge.get_full_name() if obj.judge else None

    def get_participant_name(self, obj):
        if obj.event_registration:
            if obj.event_registration.team_name:
                return obj.event_registration.team_name
            # Get first team member's name
            team_members = obj.event_registration.team_members.all()
            if team_members.exists():
                member = team_members.first()
                return f"{member.first_name} {member.last_name}".strip()
        return None

    def get_sub_event_name(self, obj):
        return obj.sub_event.name if obj.sub_event else None
    
    # def validate_criteria_scores(self, value):
    #     sub_event = self.instance.sub_event if self.instance else self.context.get('sub_event')
    #     required_criteria = sub_event.scoring_criteria.keys()
        
    #     if not all(criterion in value for criterion in required_criteria):
    #         raise serializers.ValidationError(f"Must provide scores for all criteria: {', '.join(required_criteria)}")
        
    #     return value
    
    def create(self, validated_data):
        # Calculate total score based on criteria weights
        criteria_scores = validated_data.get('criteria_scores', {})
        sub_event = self.context.get('sub_event')
        
        if sub_event and criteria_scores:
            total_score = sum(
                criteria_scores.get(criterion, 0) * sub_event.scoring_criteria.get(criterion, {}).get('weight', 1)
                for criterion in criteria_scores
            )
            validated_data['total_score'] = total_score
        
        # Create score instance
        score = super().create(validated_data)
        return score

class EventHeatSerializer(serializers.ModelSerializer):
    sub_event_name = serializers.CharField(source='sub_event.name', read_only=True)
    participant_count = serializers.SerializerMethodField()
    judges = serializers.SerializerMethodField()
    
    class Meta:
        model = EventHeat
        fields = '__all__'
    
    def get_participant_count(self, obj):
        return obj.heatparticipant_set.count()
    
    def get_judges(self, obj):
        return SubEventFacultySerializer(
            obj.sub_event.subeventfaculty_set.filter(is_active=True), 
            many=True
        ).data

class HeatParticipantSerializer(serializers.ModelSerializer):
    participant_details = EventRegistrationSerializer(source='registration', read_only=True)
    
    class Meta:
        model = HeatParticipant
        fields = ['id', 'heat', 'registration', 'participant_details', 'created_at']