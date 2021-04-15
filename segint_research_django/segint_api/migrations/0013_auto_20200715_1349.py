# Generated by Django 3.0.7 on 2020-07-15 13:49

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('segint_api', '0012_auto_20200715_1347'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='segmentationtask',
            name='id',
        ),
        migrations.AlterField(
            model_name='segmentationtask',
            name='segmentation_id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False),
        ),
    ]
