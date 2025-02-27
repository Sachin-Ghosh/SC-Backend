# events/serializers.py
from datetime import timezone
from rest_framework import serializers
from django_summernote.fields import SummernoteTextField
from .models import (
    Organization, Event, SubEvent, SubEventImage, EventRegistration,
    SubmissionFile, EventDraw, EventScore, EventHeat, SubEventFaculty,
    HeatParticipant, EventCriteria, DepartmentScore
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
    
    class Meta:
        model = SubEventFaculty
        fields = ['id', 'faculty', 'faculty_name', 'faculty_email', 
                 'sub_event', 'is_active', 'remarks']
        read_only_fields = ['assigned_at']

    def get_faculty_name(self, obj):
        return obj.faculty.get_full_name()

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

class HeatParticipantSerializer(serializers.ModelSerializer):
    participant_name = serializers.SerializerMethodField()
    department = serializers.CharField(source='registration.department')
    year = serializers.CharField(source='registration.year')
    division = serializers.CharField(source='registration.division')
    
    class Meta:
        model = HeatParticipant
        fields = '__all__'
    
    def get_participant_name(self, obj):
        return obj.registration.get_participant_display()

class EventHeatSerializer(serializers.ModelSerializer):
    participants = HeatParticipantSerializer(
        source='heatparticipant_set',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = EventHeat
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    # def validate(self, data):
    #     """
    #     Check that the heat doesn't already exist for this stage and round
    #     """
    #     sub_event = data.get('sub_event')
    #     stage = data.get('stage')
    #     round_number = data.get('round_number')

    #     # Skip validation if any required field is missing
    #     if not all([sub_event, stage, round_number]):
    #         return data

    #     # Check for existing heat only on creation
    #     if not self.instance:  # self.instance is None for creation
    #         existing_heat = EventHeat.objects.filter(
    #             sub_event=sub_event,
    #             stage=stage,
    #             round_number=round_number
    #         ).exists()
            
    #         if existing_heat:
    #             raise serializers.ValidationError(
    #                 f'Heat already exists for {stage} round {round_number}'
    #             )

    #     return data

    # def validate_schedule(self, value):
    #     """
    #     Check that schedule is not in the past
    #     """
    #     if value < timezone.now():
    #         raise serializers.ValidationError("Schedule cannot be in the past")
    #     return value

    # def validate_max_participants(self, value):
    #     """
    #     Check that max_participants is positive
    #     """
    #     if value < 2:
    #         raise serializers.ValidationError("Heat must have at least 2 participants")
    #     return value

class EventCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventCriteria
        fields = '__all__'
    
    def validate_criteria(self, value):
        """Validate criteria format"""
        for criterion, details in value.items():
            if not isinstance(details, dict):
                raise serializers.ValidationError(
                    f"Invalid criteria format for {criterion}"
                )
            if 'weight' not in details or 'max_score' not in details:
                raise serializers.ValidationError(
                    f"Missing weight or max_score for {criterion}"
                )
            
            # Validate weights sum to 1 (excluding negative marking)
            if criterion != 'Negative Marking':
                if not (0 <= details['weight'] <= 1):
                    raise serializers.ValidationError(
                        f"Weight for {criterion} must be between 0 and 1"
                    )
        
        # Check total weight
        total_weight = sum(
            details['weight'] 
            for criterion, details in value.items() 
            if criterion != 'Negative Marking'
        )
        if not (0.99 <= total_weight <= 1.01):  # Allow small floating-point errors
            raise serializers.ValidationError("Weights must sum to 1.0")
        
        return value

class DepartmentScoreSerializer(serializers.ModelSerializer):
    event_name = serializers.CharField(source='sub_event.event.name')
    sub_event_name = serializers.CharField(source='sub_event.name')
    
    class Meta:
        model = DepartmentScore
        fields = [
            'department', 'year', 'division', 'aura_points',
            'event_name', 'sub_event_name', 'updated_at'
        ]

class ScoreboardSerializer(serializers.Serializer):
    department = serializers.CharField()
    total_aura_points = serializers.IntegerField()
    total_events = serializers.IntegerField()
    sports_points = serializers.IntegerField(required=False)
    cultural_points = serializers.IntegerField(required=False)
    special_points = serializers.IntegerField(required=False)
    
    class Meta:
        fields = [
            'department', 'total_aura_points', 'total_events',
            'sports_points', 'cultural_points', 'special_points'
        ]