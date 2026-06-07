from django.db.models import Q, QuerySet

from api.models import Connection, Device, Interface, Site


class ElementNotFound(Exception):
    pass


def connections_for_interface(interface_id: int) -> QuerySet:
    try:
        interface = Interface.objects.get(pk=interface_id)
    except Interface.DoesNotExist:
        raise ElementNotFound(f"Interface {interface_id} not found.")
    return Connection.objects.filter(Q(start_target=interface) | Q(end_target=interface))


def connections_for_device(device_id: int) -> QuerySet:
    try:
        device = Device.objects.get(pk=device_id)
    except Device.DoesNotExist:
        raise ElementNotFound(f"Device {device_id} not found.")
    return Connection.objects.filter(
        Q(start_target__device=device) | Q(end_target__device=device)
    )


def connections_for_site(site_id: int) -> QuerySet:
    try:
        site = Site.objects.get(pk=site_id)
    except Site.DoesNotExist:
        raise ElementNotFound(f"Site {site_id} not found.")
    return Connection.objects.filter(
        Q(start_target__device__site=site) | Q(end_target__device__site=site)
    )
