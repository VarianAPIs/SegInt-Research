# Generated by Django 3.0.7 on 2020-07-13 17:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('segint_api', '0003_structurecomment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='feedback',
            name='structure_comments',
        ),
        migrations.AlterField(
            model_name='feedback',
            name='segmentation_id',
            field=models.CharField(max_length=200),
        ),
    ]
