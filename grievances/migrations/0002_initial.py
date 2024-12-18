# Generated by Django 5.0.1 on 2024-11-22 20:50

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('events', '0002_initial'),
        ('grievances', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='grievance',
            name='assigned_to',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_grievances', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='grievance',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='events.subevent'),
        ),
        migrations.AddField(
            model_name='grievance',
            name='submitted_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='mediafile',
            name='event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='grievance_media_files', to='events.event'),
        ),
        migrations.AddField(
            model_name='mediafile',
            name='uploaded_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grievance_media_files', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='grievance',
            name='evidence',
            field=models.ManyToManyField(blank=True, to='grievances.mediafile'),
        ),
    ]
