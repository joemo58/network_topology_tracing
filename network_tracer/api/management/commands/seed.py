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
        # site_b = Site.objects.create(name="Site Beta", description="Secondary data centre", status=Site.Status.ACTIVE)
        # site_c = Site.objects.create(name="Site Gamma", description="Planned expansion", status=Site.Status.PLANNED)

        router_a = Device.objects.create(name="Router-A1", site=site_a, serial_num="SN-RA-001")
        # switch_a = Device.objects.create(name="Switch-A1", site=site_a, serial_num="SN-SA-001")
        # router_b = Device.objects.create(name="Router-B1", site=site_b, serial_num="SN-RB-001")
        # switch_b = Device.objects.create(name="Switch-B1", site=site_b, serial_num="SN-SB-001")
        # router_c = Device.objects.create(name="Router-C1", site=site_c, serial_num="SN-RC-001")

        # ra_eth0 = Interface.objects.create(name="eth0", device=router_a, speed=1000, status=Interface.Status.UP)
        # ra_eth1 = Interface.objects.create(name="eth1", device=router_a, speed=1000, status=Interface.Status.UP)
        # sa_eth0 = Interface.objects.create(name="eth0", device=switch_a, speed=1000, status=Interface.Status.UP)
        # sa_eth1 = Interface.objects.create(name="eth1", device=switch_a, speed=100, status=Interface.Status.DOWN)
        # rb_eth0 = Interface.objects.create(name="eth0", device=router_b, speed=1000, status=Interface.Status.UP)
        # rb_eth1 = Interface.objects.create(name="eth1", device=router_b, speed=1000, status=Interface.Status.UP)
        # sb_eth0 = Interface.objects.create(name="eth0", device=switch_b, speed=1000, status=Interface.Status.UP)
        # rc_eth0 = Interface.objects.create(name="eth0", device=router_c, speed=10000, status=Interface.Status.MAINTENANCE)

        # Connection.objects.create(name="Alpha internal link", status=Connection.Status.CONNECTED, start_interface=ra_eth0, end_interface=sa_eth0)
        # Connection.objects.create(name="Alpha-Beta WAN", status=Connection.Status.CONNECTED, start_interface=ra_eth1, end_interface=rb_eth0)
        # Connection.objects.create(name="Beta internal link", status=Connection.Status.CONNECTED, start_interface=rb_eth1, end_interface=sb_eth0)
        # Connection.objects.create(name="Beta-Gamma planned link", status=Connection.Status.DISCONNECTED, start_interface=sa_eth1, end_interface=rc_eth0)

        self.stdout.write(self.style.SUCCESS("Done."))
