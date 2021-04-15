# Generated by Django 3.0.7 on 2020-07-14 12:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('segint_api', '0006_auto_20200713_2046'),
    ]

    operations = [
        migrations.CreateModel(
            name='SegmentationTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model_input', models.FileField(upload_to='segmentation/')),
                ('time_field', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
