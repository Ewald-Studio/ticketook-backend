from django.contrib import admin
from .models import (
    Service, Operator, Terminal,
    SessionConfiguration, ServiceConfigurationLimit,
    Session,
    ServiceSessionLimit,
    Ticket
)


admin.site.register(Service)
admin.site.register(Operator)
admin.site.register(Terminal)
admin.site.register(SessionConfiguration)
admin.site.register(ServiceConfigurationLimit)
admin.site.register(Session)
admin.site.register(ServiceSessionLimit)
admin.site.register(Ticket)
