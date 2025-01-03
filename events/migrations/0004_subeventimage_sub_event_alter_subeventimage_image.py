# Generated by Django 5.0.1 on 2025-01-02 17:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_alter_eventregistration_division_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='subeventimage',
            name='sub_event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='image_set', to='events.subevent'),
        ),
        migrations.AlterField(
            model_name='subeventimage',
            name='image',
            field=models.ImageField(upload_to='sub_events/images/'),
        ),
    ]
