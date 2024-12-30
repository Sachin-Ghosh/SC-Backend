# events/serializers.py
from rest_framework import serializers
from .models import (
    Organization, Event, SubEvent, SubEventImage, EventRegistration,
    SubmissionFile, EventDraw, EventScore
)
from users.serializers import UserSerializer

class OrganizationSerializer(serializers.ModelSerializer):
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
    
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ('slug', 'created_by')

class SubEventSerializer(serializers.ModelSerializer):
    images = SubEventImageSerializer(many=True, read_only=True)
    sub_heads = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = SubEvent
        fields = '__all__'
        read_only_fields = ('slug',)

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
        read_only_fields = ('registration_number', 'status')
    
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
    
    class Meta:
        model = EventScore
        fields = '__all__'
        read_only_fields = ('points_awarded',)
    
    def validate_criteria_scores(self, value):
        sub_event = self.instance.sub_event if self.instance else self.context.get('sub_event')
        required_criteria = sub_event.scoring_criteria.keys()
        
        if not all(criterion in value for criterion in required_criteria):
            raise serializers.ValidationError(f"Must provide scores for all criteria: {', '.join(required_criteria)}")
        
        return value
    
    def create(self, validated_data):
        # Calculate total score based on criteria weights
        sub_event = self.context['sub_event']
        criteria_scores = validated_data['criteria_scores']
        total_score = sum(
            criteria_scores[criterion] * sub_event.scoring_criteria[criterion]['weight']
            for criterion in criteria_scores
        )
        validated_data['total_score'] = total_score
        
        # Award points for group events if this is a winner
        if (validated_data.get('score_type') == 'WINNER' and 
            sub_event.participation_type == 'GROUP'):
            validated_data['points_awarded'] = 2
        
        return super().create(validated_data)