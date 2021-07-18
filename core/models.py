import datetime
from django.db import models
from django.db.models import constraints
from django.db.models.fields import related
from django.db.models.constraints import UniqueConstraint


class Service(models.Model):
    slug = models.SlugField(max_length=30, unique=True)
    name = models.CharField(max_length=255)
    prefix = models.CharField(max_length=3)

    def __str__(self):
        return self.name


class Operator(models.Model):
    name = models.CharField(max_length=255)
    pin = models.CharField(max_length=10)
    services_providing = models.ManyToManyField(Service, blank=True)
    is_manager = models.BooleanField(default=False)

    current_token = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return self.name


class Terminal(models.Model):
    name = models.CharField(max_length=255)
    access_key = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Zone(models.Model):
    name = models.CharField(max_length=255)
    planned_finish_time = models.TimeField(blank=True, null=True)
    services = models.ManyToManyField(Service, blank=True)
    operators = models.ManyToManyField(Operator, blank=True)
    terminals = models.ManyToManyField(Terminal, blank=True)

    def __str__(self):
        return self.name


class ServiceZoneLimit(models.Model):
    zone = models.ForeignKey(Zone, related_name='service_limits', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    max_tickets_count = models.PositiveIntegerField(default=0)


class Session(models.Model):
    date_start = models.DateTimeField(auto_now_add=True)
    date_finish = models.DateTimeField(blank=True, null=True)
    planned_finish_datetime = models.DateTimeField(blank=True, null=True)
    zone = models.ForeignKey(Zone, null=True, on_delete=models.SET_NULL)
    is_paused = models.BooleanField(default=False)

    @property
    def is_active(self):
        return (self.date_finish is None) and (self.is_paused == False)

    def pause(self):
        self.is_paused = True
        self.save()

    def finish(self):
        self.date_finish = datetime.datetime.now()
        self.is_paused = False
        self.save()

    def resume(self):
        self.date_finish = None
        self.is_paused = False
        self.save()

    def __str__(self):
        return self.date_start.strftime("%d.%m.%Y %H:%M:%S")


class ServiceSessionLimit(models.Model):
    session = models.ForeignKey(Session, related_name='service_limits', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    max_tickets_count = models.PositiveIntegerField(default=0)


class Ticket(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='tickets')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    operator = models.ForeignKey(Operator, blank=True, null=True, on_delete=models.SET_NULL)
    date_issued = models.DateTimeField(auto_now_add=True)
    date_taken = models.DateTimeField(blank=True, null=True)
    date_closed = models.DateTimeField(blank=True, null=True)

    is_active = models.BooleanField(default=False)

    number = models.PositiveIntegerField()
    is_skipped = models.BooleanField(default=False)

    @property
    def is_pending(self):
        return (self.date_closed is not None) and (self.is_skipped == False)

    @property
    def full_number(self):
        return f"{self.service.prefix}-{self.number}"

    def take(self, operator):
        self.date_closed = None
        self.date_taken = datetime.datetime.now()
        self.is_skipped = False
        self.is_active = True
        self.operator = operator
        self.save()

    def close(self):
        self.date_closed = datetime.datetime.now()
        self.is_active = False
        self.save()

    def skip(self):
        self.date_closed = datetime.datetime.now()
        self.is_active = False
        self.is_skipped = True
        self.save()

    def __str__(self):
        return self.session.date_start.strftime("%d.%m.%Y") + ' :: ' + self.full_number

    class Meta:
        constraints = [
            UniqueConstraint(fields=['session', 'service', 'number'], name='unique_number_in_session')
        ]


# class Log(models.Model):
#     pass