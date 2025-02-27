# Generated by Django 5.0.1 on 2025-01-05 10:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0018_scoreboard'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='eventheat',
            unique_together=set(),
        ),
        migrations.RenameField(
            model_name='eventheat',
            old_name='scheduled_time',
            new_name='schedule',
        ),
        migrations.AddField(
            model_name='eventheat',
            name='stage',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='eventheat',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='eventheat',
            name='max_participants',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='eventheat',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='eventheat',
            name='venue',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='eventheat',
            name='round_number',
            field=models.IntegerField(blank=True, default=1, null=True),
        ),
        migrations.AlterField(
            model_name='eventheat',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed')], max_length=20),
        ),
        migrations.RemoveField(
            model_name='eventheat',
            name='completed_time',
        ),
        migrations.RemoveField(
            model_name='eventheat',
            name='heat_number',
        ),
        migrations.RemoveField(
            model_name='eventheat',
            name='notes',
        ),
        migrations.RemoveField(
            model_name='eventheat',
            name='participants',
        ),
        migrations.AlterUniqueTogether(
            name='eventheat',
            unique_together={('sub_event', 'stage', 'round_number')},
        ),
        migrations.CreateModel(
            name='HeatParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('heat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='events.eventheat')),
                ('registration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='events.eventregistration')),
            ],
            options={
                'unique_together': {('heat', 'registration')},
            },
        ),
    ]
