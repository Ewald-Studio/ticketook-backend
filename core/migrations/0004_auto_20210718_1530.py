# Generated by Django 3.2.5 on 2021-07-18 15:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20210718_1530'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operator',
            name='zone',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='operators', to='core.zone'),
        ),
        migrations.AlterField(
            model_name='service',
            name='zone',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='services', to='core.zone'),
        ),
        migrations.AlterField(
            model_name='terminal',
            name='zone',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='terminals', to='core.zone'),
        ),
    ]