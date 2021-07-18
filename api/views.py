import json
import uuid
import datetime
from django.db import IntegrityError
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from app.core.models import (
    Service, Operator, Terminal,
    Zone,
    Session,
    ServiceSessionLimit,
    Ticket,
    Log
)


@csrf_exempt
def login(request):
    data = json.loads(request.body)
    try:
        operator = Operator.objects.get(pk=data['operator_id'])
    except Operator.DoesNotExist:
        return JsonResponse({ 'error': 'Operator with requested ID is not found' }, status=400)
    if operator.pin != data.get('pin', ''):
        return JsonResponse({ 'error': 'Invalid pin code' }, status=403)
    
    token = uuid.uuid4()
    operator.current_token = token
    operator.save()

    Log.objects.create(action='LOGIN', zone=operator.zone, operator=operator)

    response = {
        'token': token
    }
    return JsonResponse(response)


@csrf_exempt
def logout(request):
    data = json.loads(request.body)
    try:
        operator = Operator.objects.get(current_token=data['token'])
    except Operator.DoesNotExist:
        return JsonResponse({ 'error': 'No operators found for requested token' }, status=404)
    operator.current_token = None
    operator.save()

    Log.objects.create(action='LOGOUT', zone=operator.zone, operator=operator)

    response = {
        'success': True
    }
    return JsonResponse(response)


@csrf_exempt
def ticket(request):
    data = json.loads(request.body)

    # Checking request integrity
    try:
        terminal = Terminal.objects.get(access_key=data['access_key'])
        service = Service.objects.get(slug=data['service_slug'])
        session = Session.objects.get(pk=data['session_id'])
    except Terminal.DoesNotExist:
        return JsonResponse({ 'error': 'Invalid access key for terminal' }, status=401)
    except Service.DoesNotExist:
        return JsonResponse({ 'error': 'Requested service does not exist' }, status=400)
    except Session.DoesNotExist:
        return JsonResponse({ 'error': 'Requested session does not exist' }, status=400)

    # Check if terminal exists in session zone
    if not session.zone.terminals.filter(pk=terminal.pk).exists():
        return JsonResponse({ 'error': 'Terminal has no access to this session' }, status=403)

    # Checking if session is closed or paused
    if session.is_paused:
        return JsonResponse({ 'error': 'Session is paused' }, status=410)
    elif session.is_active == False:
        return JsonResponse({ 'error': 'Session is finished' }, status=410)

    # Getting queryset for pending tickets
    tickets = Ticket.objects.filter(
        session=session,
        service=service
    ).order_by('-number')

    # Checking if ticket count limit exceeded
    max_tickets_count = 0
    session_limits = session.service_limits.filter(service=service)
    zone_limits = session.zone.service_limits.filter(service=service)
    if session_limits.exists():
        max_tickets_count = session_limits[0].max_tickets_count
    elif zone_limits.exists(): 
        max_tickets_count = zone_limits[0].max_tickets_count

    if max_tickets_count > 0 and tickets.count() >= max_tickets_count:
        return JsonResponse({ 'error': 'Maximum tickets count exceeded' }, status=410)

    # Checking if planned finish datetime exceeded
    if session.planned_finish_datetime and session.planned_finish_datetime < timezone.now():
        return JsonResponse({ 'error': 'Session time is over' }, status=410)

    # Creating new ticket with fresh number
    try:
        last_ticket = tickets[0]
        last_number = last_ticket.number
    except IndexError:
        last_number = 0

    tries_remaining = 3
    running = True
    while running:
        number = last_number + 1
        try:
            ticket = Ticket.objects.create(
                session=session,
                service=service,
                number=number
            )
            running = False
        except IntegrityError:
            tries_remaining -= 1
            if tries_remaining == 0:
                return JsonResponse({ 'error': 'Ticket numbering tries number exceeded' }, status=500)

    # Getting pending tickets count
    tickets_pending = Ticket.objects.filter(
        session=session,
        date_closed__isnull=True, 
        is_skipped=False
    )

    Log.objects.create(action='TICKET-ISSUE', zone=session.zone, session=session, service=service, ticket=ticket)

    # Well done!
    response = {
        'ticket': {
            'full_number': ticket.full_number,
            'pending': tickets_pending.count() - 1,
            # 'service_pending': tickets_pending.filter(service=service).count() - 1,
        }
    }
    return JsonResponse(response)


@csrf_exempt
def operator__take(request):
    data = json.loads(request.body)

    # Checking request integrity
    try:
        operator = Operator.objects.get(current_token=data['token'])
    except Operator.DoesNotExist:
        return JsonResponse({ 'error': 'Invalid token' }, status=401)

    # Closing/skipping active ticket if exists
    try:
        current_ticket = Ticket.objects.get(operator=operator, is_active=True)
        if data.get('skip'):
            current_ticket.skip()
        else:
            current_ticket.close()
    except Ticket.DoesNotExist:
        pass

    sessions = Session.objects.filter(zone__operators=operator)

    # Taking specified ticket if operator wish to
    if data.get('ticket_id'):
        try:
            ticket = Ticket.objects.get(session__in=sessions, pk=data['ticket_id'])
        except Ticket.DoesNotExist:
            return JsonResponse({ 'error': 'Ticket with requested id does not exist' }, status=404)
        ticket.take(operator)
    
    # ... or taking next pending ticket
    else:
        services = operator.services_providing.all()
        pending_tickets = Ticket.objects.filter(
            session__in=sessions,
            date_closed__isnull=True, 
            is_skipped=False,
            is_active=False,
            service__in=services
        ).order_by('number')
        if pending_tickets.exists():
            ticket = pending_tickets[0]
            ticket.take(operator)
        else:
            return JsonResponse({ 'error': 'No tickets pending' }, status=404)

    # Ticket has been taken!
    response = {
        'ticket': {
            'id': ticket.pk,
            'full_number': ticket.full_number,
        }
    }
    return JsonResponse(response)


@csrf_exempt
def session__new(request):
    data = json.loads(request.body)

    warnings = []

    # Check if operator exists and has permission to manage sessions
    try:
        operator = Operator.objects.get(current_token=data['token'])
    except Operator.DoesNotExist:
        return JsonResponse({ 'error': 'Invalid token' }, status=401)
    if not operator.is_manager:
        return JsonResponse({ 'error': 'Operator has no permission to manage sessions' }, status=403)

    # Check if requested zone exists
    try:
        zone = Zone.objects.get(pk=data['zone_id'])
    except Zone.DoesNotExist:
        return JsonResponse({ 'error': 'Zone does not exist' }, status=400)
    except KeyError:
        return JsonResponse({ 'error': 'Invalid zone id' }, status=400)

    # Check if no active session exists
    if Session.objects.filter(zone=zone, date_finish__isnull=True).exists():
        return JsonResponse({ 'error': 'Opened session already exists' }, status=400)

    # Creating new session
    session = Session.objects.create(
        zone=zone
    )

    # Setting session finish datetime and/or service limits if given
    planned_finish_time = data.get('planned_finish_time')
    if not planned_finish_time:
        planned_finish_time = zone.planned_finish_time
    
    if planned_finish_time:
        now = datetime.datetime.now()
        planned_finish_datetime = now.replace(hour=planned_finish_time.hour, minute=planned_finish_time.minute, second=0)
        if planned_finish_datetime < now:
            planned_finish_datetime = planned_finish_datetime + datetime.timedelta(days=1)

        session.planned_finish_datetime = planned_finish_datetime
        session.save()

    service_limits = data.get('service_limits', [])
    for service_limit in service_limits:
        try:
            service = Service.objects.get(pk=service_limit['service_id'])
            ServiceSessionLimit.objects.create(
                session=session, 
                service=service, 
                max_tickets_count=service_limit['max_tickets_count']
            )
        except:
            warnings.append({ "error": "Invalid service limit data" })

    # Setting the session as active in the zone
    zone.active_session = session
    zone.save()

    Log.objects.create(
        action='SESSION-NEW', 
        zone=zone, 
        session=session,
        operator=operator
    )

    # Session is ready
    response = {
        'session': {
            'id': session.pk
        },
        'warnings': warnings
    }
    return JsonResponse(response)


@csrf_exempt
def session__action(request, session_id, action_type):
    data = json.loads(request.body)
    warnings = []

    # Check if operator exists and has permission to manage sessions
    try:
        operator = Operator.objects.get(current_token=data['token'])
    except Operator.DoesNotExist:
        return JsonResponse({ 'error': 'Invalid token' }, status=401)
    if not operator.is_manager:
        return JsonResponse({ 'error': 'Operator has no permission to manage sessions' }, status=403)

    # Check if requested session exists
    try:
        session = Session.objects.get(pk=session_id)
    except Zone.DoesNotExist:
        return JsonResponse({ 'error': 'Session does not exist' }, status=400)
    except KeyError:
        return JsonResponse({ 'error': 'Invalid session id' }, status=400)

    if action_type == 'pause':
        if session.is_paused:
            warnings.append({ 'error': 'Session was already paused' })
        session.pause(operator)
    elif action_type == 'finish':
        if session.date_finish is not None:
            warnings.append({ 'error': 'Session was already finished' })
        session.finish(operator)
    elif action_type == 'resume':
        if Session.objects.filter(zone=session.zone, date_finish__isnull=True, is_paused=False).exists():
            return JsonResponse({ 'error': 'Opened session already exists' }, status=400)
        session.resume(operator)
    elif action_type == 'skip_pending_tickets':
        tickets = session.tickets.filter(date_closed__isnull=True)
        for ticket in tickets:
            ticket.skip()
    else:
        return JsonResponse({ 'error': 'Invalid action' }, status=400)

    response = {
        'session_id': session.pk,
        'action': action_type,
        'success': True,
        'warnings': warnings
    }
    return JsonResponse(response)


def session__info(request, session_id):
    # Check if requested session exists
    try:
        session = Session.objects.get(pk=session_id)
    except Session.DoesNotExist:
        return JsonResponse({ 'error': 'Session does not exist' }, status=404)

    if session.is_active:
        status = 'active'
    elif session.is_paused:
        status = 'paused'
    elif session.planned_finish_datetime and session.planned_finish_datetime < timezone.now():
        status = 'timeout'
    else:
        status = 'finished'

    # @todo status for planned_finish_datetime exceeded?

    active_tickets = session.tickets.filter(is_active=True).order_by('-number')
    pending_tickets = session.tickets.filter(is_active=False, date_closed__isnull=True).order_by('-number')
    closed_tickets = session.tickets.filter(date_closed__isnull=False).order_by('-number')
    if not request.GET.get('full'):
        closed_tickets = closed_tickets[:10]

    def tickets_list(tickets):
        return [{
            'id': ticket.id, 
            'full_number': ticket.full_number,
            'service_id': ticket.service.pk,
            'operator_id': ticket.operator_id
        } for ticket in tickets]

    response = {
        'id': session.pk,
        'planned_finish_datetime': session.planned_finish_datetime,
        'status': status,
        'tickets': {
            'active': tickets_list(active_tickets),
            'closed': tickets_list(closed_tickets),
            'pending': tickets_list(pending_tickets),
        }
    }
    return JsonResponse(response)


def zone__info(request, zone_id):
    # Check if requested zone exists
    try:
        zone = Zone.objects.get(pk=zone_id)
    except Zone.DoesNotExist:
        return JsonResponse({ 'error': 'Zone does not exist' }, status=404)
    
    if zone.active_session:
        session_id = zone.active_session.pk
    else:
        session_id = None
    
    services = zone.services.all()
    operators = zone.operators.all()

    last_log = Log.objects.filter(zone=zone).last()
    if last_log:
        log_offset = last_log.pk
    else:
        log_offset = 0

    response = {
        'active_session_id': session_id,
        'log_offset': log_offset,
        'services': [{'id': service.id, 'name': service.name} for service in services],
        'operators': [{'id': op.id, 'name': op.name} for op in operators],        
    }
    return JsonResponse(response)


def zone__log(request, zone_id):
    # Check if requested zone exists
    try:
        zone = Zone.objects.get(pk=zone_id)
    except Zone.DoesNotExist:
        return JsonResponse({ 'error': 'Zone does not exist' }, status=404)

    limit = 30
    offset = request.GET.get('offset', 0)
    actions = request.GET.get('actions', None)

    if actions is not None:
        actions = actions.split(',')
        logs = Log.objects.filter(zone=zone, pk__gt=offset, action__in=actions)[:limit]
    else:
        logs = Log.objects.filter(zone=zone, pk__gt=offset)[:limit]

    log_list = [log.as_object() for log in logs]

    response = log_list
    return JsonResponse(response, safe=False)

