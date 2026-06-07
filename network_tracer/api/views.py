from django.db.models import ProtectedError
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.repository import ElementNotFound, connections_for_device, connections_for_interface, connections_for_site
from api.models import Connection, Device, Interface, Site
from api.serializers import ConnectionSerializer, DeviceSerializer, InterfaceSerializer, SiteSerializer


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.order_by('pk')
    serializer_class = SiteSerializer


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.select_related('site').order_by('pk')
    serializer_class = DeviceSerializer


class InterfaceViewSet(viewsets.ModelViewSet):
    queryset = Interface.objects.select_related('device').order_by('pk')
    serializer_class = InterfaceSerializer

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"error": "Cannot delete an interface that is part of a connection."},
                status=status.HTTP_409_CONFLICT,
            )


class ConnectionViewSet(viewsets.ModelViewSet):
    queryset = Connection.objects.select_related(
        'start_target__device__site',
        'end_target__device__site',
    ).order_by('pk')
    serializer_class = ConnectionSerializer


@api_view(['GET'])
def trace_connections(request):
    element_type = request.query_params.get('type')
    element_id = request.query_params.get('id')

    if not element_type or not element_id:
        return Response(
            {"error": "Both 'type' and 'id' query parameters are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if element_type not in ('site', 'device', 'interface'):
        return Response(
            {"error": "'type' must be 'site', 'device', or 'interface'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        element_id = int(element_id)
    except ValueError:
        return Response(
            {"error": "'id' must be an integer."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tracers = {
        'interface': connections_for_interface,
        'device': connections_for_device,
        'site': connections_for_site,
    }

    try:
        connections = tracers[element_type](element_id)
    except ElementNotFound as exc:
        return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)

    serializer = ConnectionSerializer(connections, many=True, context={'request': request})
    return Response(serializer.data)
