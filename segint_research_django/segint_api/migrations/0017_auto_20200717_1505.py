# Generated by Django 3.0.7 on 2020-07-17 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('segint_api', '0016_segmentationtelemetry'),
    ]

    operations = [
        migrations.AddField(
            model_name='segmentationjob',
            name='error',
            field=models.CharField(blank=True, max_length=60, null=True),
        ),
        migrations.AlterField(
            model_name='feedback',
            name='general_score',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='structurecomment',
            name='score',
            field=models.FloatField(null=True),
        ),
    ]
