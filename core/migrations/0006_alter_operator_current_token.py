# Generated by Django 3.2.5 on 2021-07-17 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_operator_current_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operator',
            name='current_token',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
