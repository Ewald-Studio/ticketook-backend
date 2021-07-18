# Generated by Django 3.2.5 on 2021-07-18 14:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Operator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('pin', models.CharField(max_length=10)),
                ('is_manager', models.BooleanField(default=False)),
                ('current_token', models.CharField(blank=True, max_length=64, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=30, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('prefix', models.CharField(max_length=3)),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_start', models.DateTimeField(auto_now_add=True)),
                ('date_finish', models.DateTimeField(blank=True, null=True)),
                ('planned_finish_datetime', models.DateTimeField(blank=True, null=True)),
                ('is_paused', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Terminal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('access_key', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Zone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('planned_finish_time', models.TimeField(blank=True, null=True)),
                ('operators', models.ManyToManyField(blank=True, to='core.Operator')),
                ('services', models.ManyToManyField(blank=True, to='core.Service')),
                ('terminals', models.ManyToManyField(blank=True, to='core.Terminal')),
            ],
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_issued', models.DateTimeField(auto_now_add=True)),
                ('date_taken', models.DateTimeField(blank=True, null=True)),
                ('date_closed', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=False)),
                ('number', models.PositiveIntegerField()),
                ('is_skipped', models.BooleanField(default=False)),
                ('operator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.operator')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.service')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to='core.session')),
            ],
        ),
        migrations.AddField(
            model_name='session',
            name='zone',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.zone'),
        ),
        migrations.CreateModel(
            name='ServiceZoneLimit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_tickets_count', models.PositiveIntegerField(default=0)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.service')),
                ('zone', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_limits', to='core.zone')),
            ],
        ),
        migrations.CreateModel(
            name='ServiceSessionLimit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_tickets_count', models.PositiveIntegerField(default=0)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.service')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_limits', to='core.session')),
            ],
        ),
        migrations.AddField(
            model_name='operator',
            name='services_providing',
            field=models.ManyToManyField(blank=True, to='core.Service'),
        ),
        migrations.AddConstraint(
            model_name='ticket',
            constraint=models.UniqueConstraint(fields=('session', 'service', 'number'), name='unique_number_in_session'),
        ),
    ]
