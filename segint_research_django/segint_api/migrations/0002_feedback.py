# Generated by Django 3.0.7 on 2020-07-13 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('segint_api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_information', models.CharField(max_length=200)),
                ('segmentation_id', models.PositiveIntegerField()),
                ('segmentation_accepted', models.BooleanField()),
                ('general_comments', models.TextField()),
                ('general_score', models.FloatField()),
                ('structure_comments', models.TextField()),
            ],
        ),
    ]
