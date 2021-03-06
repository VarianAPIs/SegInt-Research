# Generated by Django 3.0.7 on 2020-07-27 21:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('segint_api', '0021_bodypartexamined_model_family'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelChannelDescription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel_id', models.CharField(blank=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='AcceptedModality',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modality_type', models.IntegerField(blank=True, choices=[(0, 'Ct'), (1, 'Cta'), (2, 'Mr T1'), (3, 'Mr T2'), (4, 'Mr Gad'), (5, 'Mr Flair'), (6, 'Pet')], null=True)),
                ('model_channel_description', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='segint_api.ModelChannelDescription')),
            ],
        ),
    ]
