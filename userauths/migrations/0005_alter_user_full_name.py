# Generated by Django 4.2.7 on 2024-08-23 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauths', '0004_user_refresh_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='full_name',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]
