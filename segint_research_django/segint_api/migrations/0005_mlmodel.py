# Generated by Django 3.0.7 on 2020-07-13 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('segint_api', '0004_auto_20200713_1704'),
    ]

    operations = [
        migrations.CreateModel(
            name='MLModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pb', models.FileField(upload_to='models/')),
            ],
        ),
    ]