# Generated by Django 3.2.5 on 2021-07-17 13:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_terminal_access_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='operator',
            name='services_providing',
            field=models.ManyToManyField(blank=True, to='core.Service'),
        ),
        migrations.AddField(
            model_name='session',
            name='configuration',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.sessionconfiguration'),
        ),
    ]
