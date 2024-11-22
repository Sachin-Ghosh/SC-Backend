# Generated by Django 5.0.1 on 2024-11-22 20:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('events', '0001_initial'),
        ('grievances', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MediaFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='media/')),
                ('upload_date', models.DateTimeField(auto_now_add=True)),
                ('file_type', models.CharField(max_length=20)),
                ('event', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='event_media_files', to='events.event')),
                ('grievance', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='grievances.grievance')),
            ],
        ),
    ]
