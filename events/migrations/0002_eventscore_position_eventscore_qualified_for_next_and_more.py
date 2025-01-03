# Generated by Django 5.0.1 on 2025-01-01 09:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventscore',
            name='position',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='eventscore',
            name='qualified_for_next',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='eventscore',
            name='round_number',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='eventscore',
            name='time_taken',
            field=models.DurationField(null=True),
        ),
        migrations.AddField(
            model_name='subevent',
            name='current_round',
            field=models.IntegerField(blank=True, default=1, null=True),
        ),
        migrations.AddField(
            model_name='subevent',
            name='participants_per_group',
            field=models.IntegerField(blank=True, default=5, null=True),
        ),
        migrations.AddField(
            model_name='subevent',
            name='qualifiers_per_group',
            field=models.IntegerField(blank=True, default=3, null=True),
        ),
        migrations.AddField(
            model_name='subevent',
            name='round_format',
            field=models.CharField(blank=True, choices=[('ELIMINATION', 'Elimination'), ('POINTS', 'Points Based'), ('TIME', 'Time Based')], max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='subevent',
            name='total_rounds',
            field=models.IntegerField(blank=True, default=1, null=True),
        ),
        migrations.CreateModel(
            name='EventHeat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round_number', models.IntegerField(default=1)),
                ('heat_number', models.IntegerField(default=1)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('ONGOING', 'Ongoing'), ('COMPLETED', 'Completed')], default='PENDING', max_length=20)),
                ('scheduled_time', models.DateTimeField(blank=True, null=True)),
                ('completed_time', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('participants', models.ManyToManyField(related_name='heats', to='events.eventregistration')),
                ('sub_event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='events.subevent')),
            ],
            options={
                'unique_together': {('sub_event', 'round_number', 'heat_number')},
            },
        ),
        migrations.AddField(
            model_name='eventscore',
            name='heat',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='events.eventheat'),
        ),
    ]
