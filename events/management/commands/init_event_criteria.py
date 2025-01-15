from django.core.management.base import BaseCommand
from events.models import EventCriteria

class Command(BaseCommand):
    help = 'Initialize default event criteria'

    def handle(self, *args, **kwargs):
        CULTURAL_CRITERIA = {
            'Debate': {
                'Content/Argument': {'weight': 0.30, 'max_score': 10},
                'Clarity & Articulation': {'weight': 0.20, 'max_score': 10},
                'Rebuttal': {'weight': 0.20, 'max_score': 10},
                'Body Language': {'weight': 0.15, 'max_score': 10},
                'Time Management': {'weight': 0.15, 'max_score': 10},
                'Negative Marking': {'weight': -1, 'max_score': 10}
            },
            'Group Singing': {
                'Vocal Quality': {'weight': 0.30, 'max_score': 10},
                'Song Selection': {'weight': 0.20, 'max_score': 10},
                'Expression & Stage Presence': {'weight': 0.20, 'max_score': 10},
                'Rhythm & Tempo': {'weight': 0.15, 'max_score': 10},
                'Theme Relevance': {'weight': 0.15, 'max_score': 10},
                'Negative Marking': {'weight': -1, 'max_score': 10}
            },
            'Fashion Show': {
                'Theme Adherence': {'weight': 0.25, 'max_score': 10},
                'Choreography': {'weight': 0.20, 'max_score': 10},
                'Costume Design': {'weight': 0.20, 'max_score': 10},
                'Stage Presence': {'weight': 0.20, 'max_score': 10},
                'Overall Impact': {'weight': 0.15, 'max_score': 10},
                'Negative Marking': {'weight': -1, 'max_score': 10}
            },
            # Add more event criteria here
        }

        for event_name, criteria in CULTURAL_CRITERIA.items():
            EventCriteria.objects.get_or_create(
                name=event_name,
                event_type='CULTURAL',
                defaults={'criteria': criteria}
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully initialized event criteria'))