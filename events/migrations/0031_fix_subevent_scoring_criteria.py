from django.db import migrations
from events.models import SubEvent, EventCriteria

def forward_func(apps, schema_editor):
    # Get the models
    SubEvent = apps.get_model('events', 'SubEvent')
    EventCriteria = apps.get_model('events', 'EventCriteria')
    
    # Create default criteria if needed
    default_criteria = EventCriteria.objects.create(
        name="Default Criteria",
        event_type="CULTURAL",
        criteria={
            "Performance": {"weight": 1.0, "max_score": 10}
        },
        is_active=True
    )
    
    # Update all SubEvents with null scoring_criteria
    SubEvent.objects.filter(scoring_criteria__isnull=True).update(
        scoring_criteria=default_criteria
    )

def reverse_func(apps, schema_editor):
    # Get the models
    SubEvent = apps.get_model('events', 'SubEvent')
    EventCriteria = apps.get_model('events', 'EventCriteria')
    
    # Set all scoring_criteria to null
    SubEvent.objects.all().update(scoring_criteria=None)
    
    # Delete the default criteria
    EventCriteria.objects.filter(name="Default Criteria").delete()

class Migration(migrations.Migration):

    dependencies = [
        ('events', '0030_eventcriteria_alter_eventheat_options_and_more'),
    ]

    operations = [
        migrations.RunPython(forward_func, reverse_func),
    ] 