from django.contrib import admin
from .models import (
    Log, Service, Operator, Terminal,
    Zone, ServiceZoneLimit,
    Session,
    ServiceSessionLimit,
    Ticket
)


admin.site.register(Service)
admin.site.register(Operator)
admin.site.register(Terminal)
admin.site.register(Zone)
admin.site.register(ServiceZoneLimit)
admin.site.register(Session)
admin.site.register(ServiceSessionLimit)
admin.site.register(Ticket)
admin.site.register(Log)
