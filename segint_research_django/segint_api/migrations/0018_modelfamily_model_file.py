# Generated by Django 3.0.7 on 2020-07-27 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('segint_api', '0017_auto_20200717_1505'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelfamily',
            name='model_file',
            field=models.FileField(blank=True, upload_to='models/'),
        ),
    ]