# Generated by Django 5.0.1 on 2025-01-05 07:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0010_subevent_gender_participation'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='eventscore',
            options={'ordering': ['sub_event', 'stage', '-total_score']},
        ),
        migrations.AlterField(
            model_name='eventscore',
            name='event_registration',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scores', to='events.eventregistration'),
        ),
        migrations.AlterField(
            model_name='eventscore',
            name='heat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='events.eventheat'),
        ),
    ]
