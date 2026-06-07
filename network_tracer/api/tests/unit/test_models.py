from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase

from api.models import Connection, Device, Interface, Site


class SiteModelTest(TestCase):
    def test_default_status_is_active(self):
        site = Site.objects.create(name='Site A')
        self.assertEqual(site.status, Site.Status.ACTIVE)

    def test_default_description_is_empty_string(self):
        site = Site.objects.create(name='Site A')
        self.assertEqual(site.description, '')

    def test_duplicate_name_raises_integrity_error(self):
        Site.objects.create(name='Site A')
        with self.assertRaises(IntegrityError):
            Site.objects.create(name='Site A')

    def test_description_exceeding_max_length_raises_validation_error(self):
        site = Site(name='Site A', description='x' * 71)
        with self.assertRaises(ValidationError):
            site.full_clean()

    def test_invalid_status_raises_validation_error(self):
        site = Site(name='Site A', status='XX')
        with self.assertRaises(ValidationError):
            site.full_clean()


class DeviceModelTest(TestCase):
    def setUp(self):
        self.site = Site.objects.create(name='Site A')

    def test_duplicate_name_raises_integrity_error(self):
        Device.objects.create(name='Router-1', site=self.site, serial_num='SN-001')
        with self.assertRaises(IntegrityError):
            Device.objects.create(name='Router-1', site=self.site, serial_num='SN-002')

    def test_duplicate_serial_num_raises_integrity_error(self):
        Device.objects.create(name='Router-1', site=self.site, serial_num='SN-001')
        with self.assertRaises(IntegrityError):
            Device.objects.create(name='Router-2', site=self.site, serial_num='SN-001')

    def test_serial_num_exceeding_max_length_raises_validation_error(self):
        device = Device(name='Router-1', site=self.site, serial_num='x' * 51)
        with self.assertRaises(ValidationError):
            device.full_clean()

    def test_deleting_site_cascades_to_devices(self):
        Device.objects.create(name='Router-1', site=self.site, serial_num='SN-001')
        self.site.delete()
        self.assertEqual(Device.objects.count(), 0)


class InterfaceModelTest(TestCase):
    def setUp(self):
        site = Site.objects.create(name='Site A')
        self.device_a = Device.objects.create(name='Router-1', site=site, serial_num='SN-001')
        self.device_b = Device.objects.create(name='Router-2', site=site, serial_num='SN-002')

    def test_duplicate_name_on_same_device_raises_integrity_error(self):
        Interface.objects.create(name='eth0', device=self.device_a, speed=1000, status='UP')
        with self.assertRaises(IntegrityError):
            Interface.objects.create(name='eth0', device=self.device_a, speed=100, status='DO')

    def test_same_name_on_different_devices_is_allowed(self):
        Interface.objects.create(name='eth0', device=self.device_a, speed=1000, status='UP')
        iface = Interface.objects.create(name='eth0', device=self.device_b, speed=1000, status='UP')
        self.assertIsNotNone(iface.pk)

    def test_deleting_device_cascades_to_interfaces(self):
        Interface.objects.create(name='eth0', device=self.device_a, speed=1000, status='UP')
        self.device_a.delete()
        self.assertEqual(Interface.objects.count(), 0)

    def test_invalid_status_raises_validation_error(self):
        iface = Interface(name='eth0', device=self.device_a, speed=1000, status='XX')
        with self.assertRaises(ValidationError):
            iface.full_clean()


class ConnectionModelTest(TestCase):
    def setUp(self):
        site = Site.objects.create(name='Site A')
        device = Device.objects.create(name='Router-1', site=site, serial_num='SN-001')
        self.iface_a = Interface.objects.create(name='eth0', device=device, speed=1000, status='UP')
        self.iface_b = Interface.objects.create(name='eth1', device=device, speed=1000, status='UP')

    def _make_connection(self, conn_id='CONN-001', **kwargs):
        return Connection.objects.create(
            connection_id=conn_id,
            status='CON',
            start_target=self.iface_a,
            end_target=self.iface_b,
            **kwargs,
        )

    def test_duplicate_connection_id_raises_integrity_error(self):
        self._make_connection('CONN-001')
        with self.assertRaises(IntegrityError):
            self._make_connection('CONN-001')

    def test_deleting_start_interface_raises_protected_error(self):
        self._make_connection()
        with self.assertRaises(ProtectedError):
            self.iface_a.delete()

    def test_deleting_end_interface_raises_protected_error(self):
        self._make_connection()
        with self.assertRaises(ProtectedError):
            self.iface_b.delete()

    def test_name_defaults_to_empty_string(self):
        conn = self._make_connection()
        self.assertEqual(conn.name, '')

    def test_name_exceeding_max_length_raises_validation_error(self):
        conn = Connection(
            connection_id='CONN-001',
            status='CON',
            name='x' * 71,
            start_target=self.iface_a,
            end_target=self.iface_b,
        )
        with self.assertRaises(ValidationError):
            conn.full_clean()

    def test_invalid_status_raises_validation_error(self):
        conn = Connection(
            connection_id='CONN-001',
            status='XX',
            start_target=self.iface_a,
            end_target=self.iface_b,
        )
        with self.assertRaises(ValidationError):
            conn.full_clean()
