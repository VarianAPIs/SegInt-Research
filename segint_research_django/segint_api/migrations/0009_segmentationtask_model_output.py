# Generated by Django 3.0.7 on 2020-07-14 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('segint_api', '0008_segmentationtask_model_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='segmentationtask',
            name='model_output',
            field=models.FileField(blank=True, upload_to='results/'),
        ),
    ]