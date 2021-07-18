import datetime
from django.db import models
from django.db.models import constraints
from django.db.models.deletion import SET_NULL
from django.db.models.fields import related
from django.db.models.constraints import UniqueConstraint


class Service(models.Model):
    # zone = models.ForeignKey(Zone, null=True, on_delete=models.SET_NULL, related_name='services')
    slug = models.SlugField(max_length=30, unique=True)
    name = models.CharField(max_length=255)
    prefix = models.CharField(max_length=3)

    def __str__(self):
        return self.name


class Zone(models.Model):
    name = models.CharField(max_length=255)
    planned_finish_time = models.TimeField(blank=True, null=True)
    services = models.ManyToManyField(Service, blank=True)
    active_session = models.ForeignKey("Session", null=True, blank=True, on_delete=models.SET_NULL, related_name="active_in_zones")

    def __str__(self):
        return self.name



class Operator(models.Model):
    zone = models.ForeignKey(Zone, null=True, on_delete=models.SET_NULL, related_name='operators')
    name = models.CharField(max_length=255)
    pin = models.CharField(max_length=10)
    services_providing = models.ManyToManyField(Service, blank=True)
    is_manager = models.BooleanField(default=False)

    current_token = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return self.name


class Terminal(models.Model):
    zone = models.ForeignKey(Zone, null=True, on_delete=models.SET_NULL, related_name='terminals')
    name = models.CharField(max_length=255)
    access_key = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class ServiceZoneLimit(models.Model):
    zone = models.ForeignKey(Zone, related_name='service_limits', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    max_tickets_count = models.PositiveIntegerField(default=0)


class Session(models.Model):
    zone = models.ForeignKey(Zone, null=True, on_delete=models.SET_NULL)
    date_start = models.DateTimeField(auto_now_add=True)
    date_finish = models.DateTimeField(blank=True, null=True)
    planned_finish_datetime = models.DateTimeField(blank=True, null=True)
    is_paused = models.BooleanField(default=False)

    @property
    def is_active(self):
        return (self.date_finish is None) and (self.is_paused == False)

    def pause(self, operator=None):
        self.is_paused = True
        self.save()
        Log.objects.create(
            action='SESSION-PAUSE', 
            zone=self.zone, 
            session=self,
            operator=operator
        )

    def finish(self, operator=None):
        self.date_finish = datetime.datetime.now()
        self.is_paused = False
        self.save()
        Log.objects.create(
            action='SESSION-FINISH', 
            zone=self.zone, 
            session=self,
            operator=operator
        )

    def resume(self, operator=None):
        self.date_finish = None
        self.is_paused = False
        self.save()
        Log.objects.create(
            action='SESSION-RESUME', 
            zone=self.zone, 
            session=self,
            operator=operator
        )


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
        Log.objects.create(
            action='TICKET-TAKE', 
            zone=self.session.zone, 
            session=self.session,
            service=self.service,
            operator=operator, 
            ticket=self
        )

    def close(self):
        self.date_closed = datetime.datetime.now()
        self.is_active = False
        self.save()
        Log.objects.create(
            action='TICKET-CLOSE', 
            zone=self.session.zone, 
            session=self.session, 
            service=self.service,
            operator=self.operator, 
            ticket=self
        )

    def skip(self):
        self.date_closed = datetime.datetime.now()
        self.is_active = False
        self.is_skipped = True
        self.save()
        Log.objects.create(
            action='TICKET-SKIP', 
            zone=self.session.zone, 
            session=self.session, 
            service=self.service,
            operator=self.operator, 
            ticket=self
        )

    def __str__(self):
        return self.session.date_start.strftime("%d.%m.%Y") + ' :: ' + self.full_number

    class Meta:
        constraints = [
            UniqueConstraint(fields=['session', 'service', 'number'], name='unique_number_in_session')
        ]


class Log(models.Model):
    ACTIONS = (
        ('LOGIN', 'Вход оператора в систему'),
        ('LOGOUT', 'Выход оператора из системы'),
        ('TICKET-ISSUE', 'Выдача билета'),
        ('TICKET-TAKE', 'Взятие билета оператором'),
        ('TICKET-CLOSE', 'Закрытие билета'),
        ('TICKET-SKIP', 'Пропуск билета'),
        ('SESSION-NEW', 'Создание новой сессии'),
        ('SESSION-PAUSE', 'Приостановка выдачи билетов'),
        ('SESSION-RESUME', 'Возобновление выдачи билетов'),
        ('SESSION-FINISH', 'Завершение сессии'),
        ('SESSION-CHANGE', 'Редактирование настроек сессии'),
    )
    datetime = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50, choices=ACTIONS)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, null=True, blank=True, on_delete=models.CASCADE)
    terminal = models.ForeignKey(Terminal, null=True, blank=True, on_delete=models.CASCADE)
    operator = models.ForeignKey(Operator, null=True, blank=True, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.datetime.strftime("%d.%m.%Y %H:%M:%S") + ' :: ' + self.action

    def as_object(self):
        result = {
            'id': self.pk,
            'action': self.action,
            'datetime': self.datetime,
            'zone': {
                'id': self.zone_id
            }
        }

        if self.action in ('LOGIN', 'LOGOUT'):
            result['operator'] = {
                'id': self.operator_id
            }

        if self.action.startswith('TICKET'):
            result['ticket'] = {
                'id': self.ticket_id,
                'full_number': self.ticket.full_number,
            }

        if self.action == 'TICKET-TAKE':
            result['ticket']['operator'] = {
                'id': self.ticket.operator_id,
                # 'name': self.ticket.operator.name,
            }

        if self.action.startswith('SESSION'):
            result['session'] = {
                'id': self.session_id,
            }

        return result

