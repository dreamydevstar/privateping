# Generated by Django 5.0.2 on 2024-03-25 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_alter_userprofile_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='friends',
            name='accepted',
            field=models.BooleanField(default=False),
        ),
    ]
