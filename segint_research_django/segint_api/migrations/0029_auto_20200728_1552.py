# Generated by Django 3.0.7 on 2020-07-28 15:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('segint_api', '0028_auto_20200728_1508'),
    ]

    operations = [
        migrations.AlterField(
            model_name='structure',
            name='model_version',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='segint_api.ModelVersion'),
        ),
    ]
