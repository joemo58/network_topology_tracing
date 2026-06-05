from rest_framework import serializers
from api.models import Connection, Device, Interface, Site

class SiteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Site
        fields = ["url", "name", "description", "status"]


class DeviceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Device
        fields = ["url", "name", "site", "serial_num"]


class InterfaceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Interface
        fields = ["url", "name", "device", "speed", "status"]


class ConnectionEndpointSerializer(serializers.Serializer):
    site = serializers.CharField()
    device = serializers.CharField()
    interface = serializers.CharField()

    def validate(self, data):
        try:
            interface = Interface.objects.get(
                name=data["interface"],
                device__name=data["device"],
                device__site__name=data["site"],
            )
        except Interface.DoesNotExist:
            raise serializers.ValidationError(
                f"No interface '{data['interface']}' on device '{data['device']}' at site '{data['site']}'"
            )
        data["_resolved"] = interface
        return data


class ConnectionSerializer(serializers.HyperlinkedModelSerializer):
    start = ConnectionEndpointSerializer(write_only=True)
    end = ConnectionEndpointSerializer(write_only=True)

    class Meta:
        model = Connection
        fields = ["url", "connection_id", "name", "status", "start", "end",
                  "start_interface", "end_interface"]
        read_only_fields = ["connection_id", "start_interface", "end_interface"]

    def create(self, validated_data):
        start_iface = validated_data.pop("start")["_resolved"]
        end_iface = validated_data.pop("end")["_resolved"]
        return Connection.objects.create(
            start_interface=start_iface, end_interface=end_iface, **validated_data
        )

    def update(self, instance, validated_data):
        if "start" in validated_data:
            instance.start_interface = validated_data.pop("start")["_resolved"]
        if "end" in validated_data:
            instance.end_interface = validated_data.pop("end")["_resolved"]
        return super().update(instance, validated_data)
