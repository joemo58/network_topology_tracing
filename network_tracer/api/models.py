from django.db import models
import uuid

class Site(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'AC', 'ACTIVE'
        PLANNED = 'PL', 'PLANNED'
        DECOMMISSIONED = 'DE', 'DECOMISSIONED'

    name = models.CharField(unique=True, primary_key=True)
    description = models.CharField(max_length=70, blank=True, default="")
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.ACTIVE)


class Device(models.Model):
    name = models.CharField(unique=True, primary_key=True)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    serial_num = models.CharField(max_length=50, unique=True)


class Interface(models.Model):
    class Status(models.TextChoices):
        UP = 'UP', 'UP'
        DOWN = 'DO', 'DOWN'
        MAINTENANCE = 'MA', 'MAINTENANCE'

    name = models.CharField()
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    speed = models.IntegerField()
    status = models.CharField(max_length=2, choices=Status.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="unique_name",
                fields=["name", "device"]
            )
        ]


class Connection(models.Model):
    class Status(models.TextChoices):
        CONNECTED = 'CON', 'CONNECTED'
        DISCONNECTED = 'DIS', 'DISCONNECTED'
    connection_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=70, blank=True, default="")
    status = models.CharField(max_length=3, choices=Status.choices)
    # prevent deleting Devices/Interfaces while Interface is part of a connection
    start_interface = models.ForeignKey(Interface, related_name='connection_starts', on_delete=models.PROTECT)
    end_interface = models.ForeignKey(Interface, related_name='connection_ends', on_delete=models.PROTECT)