# Generated by Django 5.0.1 on 2024-12-30 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='year_of_study',
            field=models.TextField(blank=True, choices=[('FE', 'FE'), ('SE', 'SE'), ('TE', 'TE'), ('BE', 'BE')], null=True),
        ),
    ]
