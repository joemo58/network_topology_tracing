from rest_framework import serializers
from api.models import Connection, Device, Interface, Site

class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ["name", "description", "status"]


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["name", "site", "serial_num"]


class InterfaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interface
        fields = ["name", "device", "speed", "status"]


class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = ["connection_id", "name", "status", 
                  "start_interface", "end_interface"] 

