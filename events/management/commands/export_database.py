from django.core.management.base import BaseCommand
from django.apps import apps
from datetime import datetime
import csv
import os
from events.models import Event, SubEvent, EventRegistration, EventHeat, HeatParticipant, EventScore, DepartmentScore
from users.models import User, CouncilMember
from grievances.models import Grievance, MediaFile

class Command(BaseCommand):
    help = 'Export all database tables to CSV files'

    def handle(self, *args, **options):
        try:
            # Create exports directory
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_dir = f'exports/database_export_{timestamp}'
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)

            # Export Users and Council Members
            self.export_users(export_dir)
            self.export_council_members(export_dir)
            
            # Export Events and SubEvents
            self.export_events(export_dir)
            self.export_sub_events(export_dir)
            
            # Export Registrations and related data
            self.export_registrations(export_dir)
            self.export_heats(export_dir)
            self.export_heat_participants(export_dir)
            self.export_scores(export_dir)
            self.export_department_scores(export_dir)
            
            # Export Grievances and Media Files
            self.export_grievances(export_dir)
            self.export_media_files(export_dir)

            self.stdout.write(
                self.style.SUCCESS(f'Successfully exported all data to {export_dir}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during export: {str(e)}')
            )

    def export_council_members(self, export_dir):
        """Export council members data"""
        fields = ['id', 'user_id', 'position']
        
        with open(os.path.join(export_dir, 'council_members.csv'), 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(fields)
            
            for member in CouncilMember.objects.all():
                writer.writerow([
                    member.id,
                    member.user_id,
                    member.position
                ])

    def export_users(self, export_dir):
        """Export users data"""
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'department', 
                 'year_of_study', 'division', 'roll_number', 'user_type', 'is_active']
        
        with open(os.path.join(export_dir, 'users.csv'), 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(fields)
            
            for user in User.objects.all():
                writer.writerow([
                    user.id, user.email, user.first_name, user.last_name, user.phone,
                    user.department, user.year_of_study, user.division, user.roll_number,
                    user.user_type, user.is_active
                ])

    def export_events(self, export_dir):
        """Export events data"""
        fields = ['id', 'name', 'description', 'start_date', 'end_date', 'is_active']
        
        with open(os.path.join(export_dir, 'events.csv'), 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(fields)
            
            for event in Event.objects.all():
                writer.writerow([
                    event.id, event.name, event.description, event.start_date,
                    event.end_date, event.is_active
                ])

    def export_sub_events(self, export_dir):
        """Export sub-events data"""
        fields = ['id', 'event_id', 'name', 'description', 'participation_type', 
                 'max_participants', 'current_stage', 'scoring_criteria', 'aura_points_winner',
                 'aura_points_runner']
        
        with open(os.path.join(export_dir, 'sub_events.csv'), 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(fields)
            
            for sub_event in SubEvent.objects.all():
                writer.writerow([
                    sub_event.id, sub_event.event_id, sub_event.name, 
                    sub_event.description, sub_event.participation_type,
                    sub_event.max_participants, sub_event.current_stage,
                    str(sub_event.scoring_criteria), sub_event.aura_points_winner,
                    sub_event.aura_points_runner
                ])

    def export_registrations(self, export_dir):
        """Export registrations data"""
        fields = ['id', 'registration_number', 'sub_event_id', 'team_name',
                 'department', 'year', 'division', 'status', 'current_stage']
        
        with open(os.path.join(export_dir, 'registrations.csv'), 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(fields)
            
            for reg in EventRegistration.objects.all():
                writer.writerow([
                    reg.id, reg.registration_number, reg.sub_event_id,
                    reg.team_name, reg.department, reg.year, reg.division,
                    reg.status, reg.current_stage
                ])

    def export_heats(self, export_dir):
        """Export heats data"""
        fields = ['id', 'sub_event_id', 'heat_number', 'heat_name', 'stage', 
                 'round_number', 'venue', 'schedule', 'max_participants', 'status']
        
        with open(os.path.join(export_dir, 'heats.csv'), 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(fields)
            
            for heat in EventHeat.objects.all():
                writer.writerow([
                    heat.id, heat.sub_event_id, heat.heat_number, heat.heat_name,
                    heat.stage, heat.round_number, heat.venue, heat.schedule,
                    heat.max_participants, heat.status
                ])

    def export_heat_participants(self, export_dir):
        """Export heat participants data"""
        fields = ['id', 'heat_id', 'registration_id', 'position']
        
        with open(os.path.join(export_dir, 'heat_participants.csv'), 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(fields)
            
            for participant in HeatParticipant.objects.all():
                writer.writerow([
                    participant.id, participant.heat_id, 
                    participant.registration_id, participant.position
                ])

    def export_scores(self, export_dir):
        """Export scores data"""
        fields = ['id', 'sub_event_id', 'event_registration_id', 'heat_id',
                 'judge_id', 'criteria_scores', 'total_score', 'position',
                 'aura_points']
        
        with open(os.path.join(export_dir, 'scores.csv'), 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(fields)
            
            for score in EventScore.objects.all():
                writer.writerow([
                    score.id, score.sub_event_id, score.event_registration_id,
                    score.heat_id, score.judge_id, str(score.criteria_scores),
                    score.total_score, score.position, score.aura_points
                ])

    def export_department_scores(self, export_dir):
        """Export department scores data"""
        fields = ['id', 'department', 'year', 'division', 'sub_event_id',
                 'total_score', 'aura_points']
        
        with open(os.path.join(export_dir, 'department_scores.csv'), 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(fields)
            
            for dept_score in DepartmentScore.objects.all():
                writer.writerow([
                    dept_score.id, dept_score.department, dept_score.year,
                    dept_score.division, dept_score.sub_event_id,
                    dept_score.total_score, dept_score.aura_points
                ])

    def export_grievances(self, export_dir):
        """Export grievances data"""
        fields = ['id', 'event_id', 'submitted_by_id', 'grievance_type', 'title',
                 'description', 'submission_date', 'status', 'assigned_to_id',
                 'resolution', 'resolved_date']
        
        with open(os.path.join(export_dir, 'grievances.csv'), 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(fields)
            
            for grievance in Grievance.objects.all():
                writer.writerow([
                    grievance.id, grievance.event_id, grievance.submitted_by_id,
                    grievance.grievance_type, grievance.title, grievance.description,
                    grievance.submission_date, grievance.status,
                    grievance.assigned_to_id, grievance.resolution,
                    grievance.resolved_date
                ])

    def export_media_files(self, export_dir):
        """Export media files data"""
        fields = ['id', 'file', 'file_type', 'description', 'size', 'is_public',
                 'upload_date', 'event_id', 'uploaded_by_id']
        
        with open(os.path.join(export_dir, 'media_files.csv'), 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(fields)
            
            for media in MediaFile.objects.all():
                writer.writerow([
                    media.id, media.file, media.file_type, media.description,
                    media.size, media.is_public, media.upload_date,
                    media.event_id, media.uploaded_by_id
                ]) 