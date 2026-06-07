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
    site = serializers.SerializerMethodField()
    device = serializers.SerializerMethodField()
    interface = serializers.SerializerMethodField()

    def get_site(self, obj):  # obj is an Interface instance
        return {"id": obj.device.id, "name": obj.device.site.name}

    def get_device(self, obj):
        return {"id": obj.device.id, "name": obj.device.name}

    def get_interface(self, obj):
        return {"id": str(obj.id), "name": obj.name}

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
    start_target = ConnectionEndpointSerializer()
    end_target = ConnectionEndpointSerializer()

    class Meta:
        model = Connection
        fields = ["url", "connection_id", "name", "status",
                  "start_target", "end_target"]
        read_only_fields = ["connection_id", "start_target", "end_target"]

    def create(self, validated_data):
        start_target = validated_data.pop("start_target")["_resolved"]
        end_iface = validated_data.pop("end_target")["_resolved"]
        return Connection.objects.create(
            start_target=start_target, end_target=end_iface, **validated_data
        )

    def update(self, instance, validated_data):
        if "start" in validated_data:
            instance.start_target = validated_data.pop("start_target")["_resolved"]
        if "end" in validated_data:
            instance.end_target = validated_data.pop("end_target")["_resolved"]
        return super().update(instance, validated_data)