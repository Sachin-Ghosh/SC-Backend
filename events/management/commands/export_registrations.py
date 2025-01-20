from django.core.management.base import BaseCommand
from django.db.models import Max
from events.models import SubEvent, EventRegistration
from datetime import datetime
import csv
import os

class Command(BaseCommand):
    help = 'Export registrations for all sub-events to separate CSV files'

    def handle(self, *args, **options):
        try:
            # Create exports directory if it doesn't exist
            export_dir = 'exports'
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_path = os.path.join(export_dir, f'registrations_{timestamp}')
            
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            if not os.path.exists(export_path):
                os.makedirs(export_path)

            # Get all sub events
            sub_events = SubEvent.objects.all().order_by('name')
            
            for sub_event in sub_events:
                # Create file name
                safe_name = "".join(x for x in sub_event.name if x.isalnum() or x in (' ','-','_'))
                file_name = f'{safe_name}_{timestamp}.csv'
                file_path = os.path.join(export_path, file_name)
                
                with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    
                    # Write event information
                    writer.writerow(['Event Information'])
                    writer.writerow(['Sub Event Name', sub_event.name])
                    writer.writerow(['Event Type', sub_event.participation_type])
                    writer.writerow(['Category', sub_event.category])
                    writer.writerow([])  # Empty row for spacing
                    
                    # Write headers
                    headers = [
                        'Registration No.',
                        'Team Name' if sub_event.participation_type == 'GROUP' else 'Participant Name',
                        'Department',
                        'Year',
                        'Division',
                        'Contact Number',
                        'Email',
                        'Roll Numbers',
                        'Status',
                        'Current Stage',
                    ]
                    
                    # Add team-specific headers for team events
                    if sub_event.participation_type == 'GROUP':
                        headers.extend([
                            'Team Members',
                            'Members Departments',
                            'Members Years',
                            'Members Divisions',
                            'Members Roll Numbers'
                        ])
                        
                    writer.writerow(headers)
                    
                    # Get latest registrations (removing duplicates)
                    registrations = EventRegistration.objects.filter(
                        sub_event=sub_event
                    )
                    
                    
                    registrations = EventRegistration.objects.filter(
                        id__in=registrations
                    ).order_by('registration_number')
                    
                    # Write registration data
                    for reg in registrations:
                        team_members = reg.team_members.all().order_by('first_name')
                        
                        if not team_members:
                            continue  # Skip if no team members found
                            
                        # For both SOLO and TEAM events, get the first member's details
                        first_member = team_members.first()
                        
                        # Base row data (common for both SOLO and TEAM)
                        row = [
                            reg.registration_number,
                            reg.team_name if sub_event.participation_type == 'GROUP' else f"{first_member.first_name} {first_member.last_name}",
                            first_member.department,
                            first_member.year_of_study,
                            first_member.division,
                            first_member.phone,
                            first_member.email,
                            first_member.roll_number,
                            reg.status,
                            reg.current_stage,
                        ]
                        
                        # Add team-specific data for team events
                        if sub_event.participation_type == 'GROUP':
                            members_info = [f"{m.first_name} {m.last_name}" for m in team_members]
                            departments = [m.department for m in team_members]
                            years = [m.year_of_study for m in team_members]
                            divisions = [m.division for m in team_members]
                            roll_numbers = [m.roll_number for m in team_members]
                            
                            row.extend([
                                ' | '.join(members_info),
                                ' | '.join(str(d) for d in departments),
                                ' | '.join(str(y) for y in years),
                                ' | '.join(str(d) for d in divisions),
                                ' | '.join(str(r) for r in roll_numbers),
                            ])
                            
                        writer.writerow(row)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully exported registrations for {sub_event.name} to {file_path}')
                )
                
            self.stdout.write(
                self.style.SUCCESS(f'All exports completed. Files saved in {export_path}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during export: {str(e)}')
            ) 