# Generated by Django 3.0.7 on 2020-07-27 21:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('segint_api', '0023_auto_20200727_2118'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modelchanneldescription',
            name='dimensions_max_x',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='modelchanneldescription',
            name='dimensions_max_y',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='modelchanneldescription',
            name='dimensions_max_z',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='modelchanneldescription',
            name='dimensions_min_x',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='modelchanneldescription',
            name='dimensions_min_y',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='modelchanneldescription',
            name='dimensions_min_z',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='modelchanneldescription',
            name='spacing_max_x',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='modelchanneldescription',
            name='spacing_max_y',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='modelchanneldescription',
            name='spacing_max_z',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='modelchanneldescription',
            name='spacing_min_x',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='modelchanneldescription',
            name='spacing_min_y',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='modelchanneldescription',
            name='spacing_min_z',
            field=models.IntegerField(default=0),
        ),
    ]
