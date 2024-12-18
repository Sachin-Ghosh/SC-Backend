# Generated by Django 5.0.1 on 2024-11-22 20:50

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('submission_date', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('IN_PROGRESS', 'In Progress'), ('RESOLVED', 'Resolved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=20)),
                ('is_anonymous', models.BooleanField(default=False)),
                ('attachment', models.FileField(blank=True, null=True, upload_to='feedback/')),
            ],
        ),
        migrations.CreateModel(
            name='FeedbackCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='FeedbackResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response', models.TextField()),
                ('response_date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
