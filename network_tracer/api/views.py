from rest_framework import viewsets
from api.models import Connection, Device, Interface, Site
from api.serializers import ConnectionSerializer, DeviceSerializer, InterfaceSerializer, SiteSerializer
from rest_framework.decorators import action

class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer


class InterfaceViewSet(viewsets.ModelViewSet):
    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer


class ConnectionViewSet(viewsets.ModelViewSet):
    queryset = Connection.objects.all()
    serializer_class = ConnectionSerializer

# custom endpoint here
# query params: type + id
