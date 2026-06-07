from django.test import TestCase
from rest_framework.test import APIRequestFactory

from api.models import Connection, Device, Interface, Site
from api.serializers import (
    ConnectionEndpointSerializer,
    ConnectionSerializer,
    DeviceSerializer,
    InterfaceSerializer,
    SiteSerializer,
)


def make_context():
    return {'request': APIRequestFactory().get('/')}


class SiteSerializerTest(TestCase):
    def setUp(self):
        self.site = Site.objects.create(name='Site A', description='Primary DC', status='AC')
        self.context = make_context()

    def test_serializes_all_fields(self):
        data = SiteSerializer(self.site, context=self.context).data
        self.assertEqual(data['name'], 'Site A')
        self.assertEqual(data['description'], 'Primary DC')
        self.assertEqual(data['status'], 'AC')
        self.assertIn('url', data)

    def test_valid_data_passes(self):
        s = SiteSerializer(data={'name': 'Site B', 'status': 'PL'}, context=self.context)
        self.assertTrue(s.is_valid(), s.errors)

    def test_description_defaults_to_empty_string(self):
        s = SiteSerializer(data={'name': 'Site C', 'status': 'AC'}, context=self.context)
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.save().description, '')

    def test_invalid_status_fails(self):
        s = SiteSerializer(data={'name': 'Site D', 'status': 'XX'}, context=self.context)
        self.assertFalse(s.is_valid())
        self.assertIn('status', s.errors)

    def test_duplicate_name_fails(self):
        s = SiteSerializer(data={'name': 'Site A', 'status': 'AC'}, context=self.context)
        self.assertFalse(s.is_valid())
        self.assertIn('name', s.errors)


class DeviceSerializerTest(TestCase):
    def setUp(self):
        self.site = Site.objects.create(name='Site A', status='AC')
        self.device = Device.objects.create(name='Router-1', site=self.site, serial_num='SN-001')
        self.context = make_context()
        self.site_url = f'http://testserver/sites/{self.site.pk}/'

    def test_serializes_all_fields(self):
        data = DeviceSerializer(self.device, context=self.context).data
        self.assertEqual(data['name'], 'Router-1')
        self.assertEqual(data['serial_num'], 'SN-001')
        self.assertIn('url', data)
        self.assertIn('site', data)

    def test_valid_data_passes(self):
        s = DeviceSerializer(
            data={'name': 'Switch-1', 'site': self.site_url, 'serial_num': 'SN-002'},
            context=self.context,
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_duplicate_serial_num_fails(self):
        s = DeviceSerializer(
            data={'name': 'Switch-2', 'site': self.site_url, 'serial_num': 'SN-001'},
            context=self.context,
        )
        self.assertFalse(s.is_valid())
        self.assertIn('serial_num', s.errors)


class InterfaceSerializerTest(TestCase):
    def setUp(self):
        self.site = Site.objects.create(name='Site A', status='AC')
        self.device = Device.objects.create(name='Router-1', site=self.site, serial_num='SN-001')
        self.interface = Interface.objects.create(name='eth0', device=self.device, speed=1000, status='UP')
        self.context = make_context()
        self.device_url = f'http://testserver/devices/{self.device.pk}/'

    def test_serializes_all_fields(self):
        data = InterfaceSerializer(self.interface, context=self.context).data
        self.assertEqual(data['name'], 'eth0')
        self.assertEqual(data['speed'], 1000)
        self.assertEqual(data['status'], 'UP')
        self.assertIn('url', data)
        self.assertIn('device', data)

    def test_valid_data_passes(self):
        s = InterfaceSerializer(
            data={'name': 'eth1', 'device': self.device_url, 'speed': 100, 'status': 'DO'},
            context=self.context,
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_status_fails(self):
        s = InterfaceSerializer(
            data={'name': 'eth2', 'device': self.device_url, 'speed': 100, 'status': 'XX'},
            context=self.context,
        )
        self.assertFalse(s.is_valid())
        self.assertIn('status', s.errors)


class ConnectionEndpointSerializerTest(TestCase):
    def setUp(self):
        self.site = Site.objects.create(name='Site A', status='AC')
        self.device = Device.objects.create(name='Router-1', site=self.site, serial_num='SN-001')
        self.interface = Interface.objects.create(name='eth0', device=self.device, speed=1000, status='UP')

    def test_to_representation_returns_nested_structure(self):
        data = ConnectionEndpointSerializer(self.interface).data
        self.assertEqual(data['site'], {'id': self.site.pk, 'name': 'Site A'})
        self.assertEqual(data['device'], {'id': self.device.pk, 'name': 'Router-1'})
        self.assertEqual(data['interface'], {'id': self.interface.pk, 'name': 'eth0'})

    def test_validate_resolves_interface(self):
        s = ConnectionEndpointSerializer(data={
            'site': 'Site A', 'device': 'Router-1', 'interface': 'eth0',
        })
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['_resolved'], self.interface)

    def test_validate_raises_for_wrong_interface_name(self):
        s = ConnectionEndpointSerializer(data={
            'site': 'Site A', 'device': 'Router-1', 'interface': 'eth99',
        })
        self.assertFalse(s.is_valid())
        self.assertIn('non_field_errors', s.errors)

    def test_validate_raises_for_wrong_device(self):
        s = ConnectionEndpointSerializer(data={
            'site': 'Site A', 'device': 'NoSuchDevice', 'interface': 'eth0',
        })
        self.assertFalse(s.is_valid())
        self.assertIn('non_field_errors', s.errors)


class ConnectionSerializerTest(TestCase):
    def setUp(self):
        self.site = Site.objects.create(name='Site A', status='AC')
        self.device = Device.objects.create(name='Router-1', site=self.site, serial_num='SN-001')
        self.iface_a = Interface.objects.create(name='eth0', device=self.device, speed=1000, status='UP')
        self.iface_b = Interface.objects.create(name='eth1', device=self.device, speed=1000, status='UP')
        self.connection = Connection.objects.create(
            connection_id='CONN-001',
            name='Test Link',
            status='CON',
            start_target=self.iface_a,
            end_target=self.iface_b,
        )
        self.context = make_context()

    def _endpoint(self, interface_name):
        return {'site': 'Site A', 'device': 'Router-1', 'interface': interface_name}

    def test_serializes_nested_endpoints(self):
        data = ConnectionSerializer(self.connection, context=self.context).data
        self.assertEqual(data['connection_id'], 'CONN-001')
        self.assertEqual(data['name'], 'Test Link')
        self.assertEqual(data['status'], 'CON')
        self.assertEqual(data['start_target']['interface']['name'], 'eth0')
        self.assertEqual(data['end_target']['interface']['name'], 'eth1')

    def test_create_resolves_interfaces(self):
        s = ConnectionSerializer(data={
            'connection_id': 'CONN-002',
            'name': 'New Link',
            'status': 'CON',
            'start_target': self._endpoint('eth0'),
            'end_target': self._endpoint('eth1'),
        }, context=self.context)
        self.assertTrue(s.is_valid(), s.errors)
        conn = s.save()
        self.assertEqual(conn.start_target, self.iface_a)
        self.assertEqual(conn.end_target, self.iface_b)

    def test_update_start_target(self):
        s = ConnectionSerializer(
            self.connection,
            data={'start_target': self._endpoint('eth1')},
            partial=True,
            context=self.context,
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.save().start_target, self.iface_b)

    def test_update_end_target(self):
        s = ConnectionSerializer(
            self.connection,
            data={'end_target': self._endpoint('eth0')},
            partial=True,
            context=self.context,
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.save().end_target, self.iface_a)
