# Generated by Django 5.0.1 on 2025-01-03 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0006_subevent_short_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='subevent',
            name='format_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='subevent',
            name='prize_pool_description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
