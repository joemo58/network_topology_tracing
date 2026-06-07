from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import Connection, Device, Interface, Site


class Command(BaseCommand):
    help = "Seed the database with sample data"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")
        Connection.objects.all().delete()
        Interface.objects.all().delete()
        Device.objects.all().delete()
        Site.objects.all().delete()

        site_a = Site.objects.create(name="Site Alpha", description="Primary data centre", status=Site.Status.ACTIVE)

        router_a = Device.objects.create(name="Router-A1", site=site_a, serial_num="SN-RA-001")
        switch_a = Device.objects.create(name="Switch-A1", site=site_a, serial_num="SN-SA-001")

        ra_eth0 = Interface.objects.create(name="eth0", device=router_a, speed=1000, status=Interface.Status.UP)
        sa_eth0 = Interface.objects.create(name="eth0", device=switch_a, speed=1000, status=Interface.Status.UP)

        Connection.objects.create(connection_id="CONN-1002", name="Core Switch Uplink", status=Connection.Status.CONNECTED, start_target=ra_eth0, end_target=sa_eth0)

        self.stdout.write(self.style.SUCCESS("Done."))
