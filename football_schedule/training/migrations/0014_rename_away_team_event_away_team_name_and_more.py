# Generated by Django 5.0.6 on 2024-06-17 11:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0013_event_away_team_event_away_team_crest_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='event',
            old_name='away_team',
            new_name='away_team_name',
        ),
        migrations.RenameField(
            model_name='event',
            old_name='home_team',
            new_name='home_team_name',
        ),
    ]
