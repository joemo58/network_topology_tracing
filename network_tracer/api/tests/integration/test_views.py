import uuid

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Connection, Device, Interface, Site


def make_site(name='Site A', status='AC'):
    return Site.objects.create(name=name, status=status)


def make_device(site, name='Router-1', serial='SN-001'):
    return Device.objects.create(name=name, site=site, serial_num=serial)


def make_interface(device, name='eth0', speed=1000, iface_status='UP'):
    return Interface.objects.create(name=name, device=device, speed=speed, status=iface_status)


def make_connection(start, end, conn_id=None, conn_status='CON'):
    if conn_id is None:
        conn_id = str(uuid.uuid4())[:8]
    return Connection.objects.create(
        connection_id=conn_id, start_target=start, end_target=end, status=conn_status
    )


class SiteViewSetTest(APITestCase):
    def setUp(self):
        self.site = make_site('Site A')

    def test_list_sites(self):
        response = self.client.get('/sites/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [s['name'] for s in response.data['results']]
        self.assertIn('Site A', names)

    def test_retrieve_site(self):
        response = self.client.get(f'/sites/{self.site.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Site A')

    def test_create_site(self):
        response = self.client.post('/sites/', {'name': 'Site B', 'status': 'PL'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Site.objects.filter(name='Site B').exists())

    def test_update_site(self):
        response = self.client.patch(
            f'/sites/{self.site.pk}/', {'description': 'Updated'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.site.refresh_from_db()
        self.assertEqual(self.site.description, 'Updated')

    def test_delete_site(self):
        response = self.client.delete(f'/sites/{self.site.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Site.objects.filter(pk=self.site.pk).exists())

    def test_create_site_with_duplicate_name_fails(self):
        response = self.client.post('/sites/', {'name': 'Site A', 'status': 'AC'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_nonexistent_site_returns_404(self):
        response = self.client.get('/sites/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DeviceViewSetTest(APITestCase):
    def setUp(self):
        self.site = make_site()
        self.device = make_device(self.site)
        self.site_url = f'http://testserver/sites/{self.site.pk}/'

    def test_list_devices(self):
        response = self.client.get('/devices/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [d['name'] for d in response.data['results']]
        self.assertIn('Router-1', names)

    def test_retrieve_device(self):
        response = self.client.get(f'/devices/{self.device.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Router-1')

    def test_create_device(self):
        response = self.client.post(
            '/devices/',
            {'name': 'Switch-1', 'site': self.site_url, 'serial_num': 'SN-002'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Device.objects.filter(name='Switch-1').exists())

    def test_update_device(self):
        response = self.client.patch(
            f'/devices/{self.device.pk}/', {'serial_num': 'SN-999'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.device.refresh_from_db()
        self.assertEqual(self.device.serial_num, 'SN-999')

    def test_delete_device(self):
        response = self.client.delete(f'/devices/{self.device.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Device.objects.filter(pk=self.device.pk).exists())

    def test_create_device_with_duplicate_serial_fails(self):
        response = self.client.post(
            '/devices/',
            {'name': 'Switch-2', 'site': self.site_url, 'serial_num': 'SN-001'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class InterfaceViewSetTest(APITestCase):
    def setUp(self):
        self.site = make_site()
        self.device = make_device(self.site)
        self.interface = make_interface(self.device)
        self.device_url = f'http://testserver/devices/{self.device.pk}/'

    def test_list_interfaces(self):
        response = self.client.get('/interfaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [i['name'] for i in response.data['results']]
        self.assertIn('eth0', names)

    def test_retrieve_interface(self):
        response = self.client.get(f'/interfaces/{self.interface.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'eth0')

    def test_create_interface(self):
        response = self.client.post(
            '/interfaces/',
            {'name': 'eth1', 'device': self.device_url, 'speed': 100, 'status': 'DO'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Interface.objects.filter(name='eth1', device=self.device).exists())

    def test_update_interface_status(self):
        response = self.client.patch(
            f'/interfaces/{self.interface.pk}/', {'status': 'MA'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.interface.refresh_from_db()
        self.assertEqual(self.interface.status, 'MA')

    def test_delete_interface_blocked_when_in_connection(self):
        iface_b = make_interface(self.device, name='eth1')
        make_connection(self.interface, iface_b, 'CONN-001')
        response = self.client.delete(f'/interfaces/{self.interface.pk}/')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Interface.objects.filter(pk=self.interface.pk).exists())


class ConnectionViewSetTest(APITestCase):
    def setUp(self):
        site = make_site()
        device = make_device(site)
        self.iface_a = make_interface(device, name='eth0')
        self.iface_b = make_interface(device, name='eth1')
        self.connection = make_connection(self.iface_a, self.iface_b, 'CONN-001')

    def _endpoint(self, iface_name):
        return {'site': 'Site A', 'device': 'Router-1', 'interface': iface_name}

    def test_list_connections(self):
        response = self.client.get('/connections/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [c['connection_id'] for c in response.data['results']]
        self.assertIn('CONN-001', ids)

    def test_retrieve_connection(self):
        response = self.client.get(f'/connections/{self.connection.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['connection_id'], 'CONN-001')
        self.assertEqual(response.data['start_target']['interface']['name'], 'eth0')
        self.assertEqual(response.data['end_target']['interface']['name'], 'eth1')

    def test_create_connection(self):
        response = self.client.post(
            '/connections/',
            {
                'connection_id': 'CONN-002',
                'name': 'New Link',
                'status': 'CON',
                'start_target': self._endpoint('eth0'),
                'end_target': self._endpoint('eth1'),
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Connection.objects.filter(connection_id='CONN-002').exists())

    def test_update_connection_name(self):
        response = self.client.patch(
            f'/connections/{self.connection.pk}/', {'name': 'Renamed'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.name, 'Renamed')

    def test_delete_connection(self):
        response = self.client.delete(f'/connections/{self.connection.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Connection.objects.filter(pk=self.connection.pk).exists())

    def test_create_connection_with_invalid_interface_fails(self):
        response = self.client.post(
            '/connections/',
            {
                'connection_id': 'CONN-003',
                'status': 'CON',
                'start_target': self._endpoint('eth99'),
                'end_target': self._endpoint('eth1'),
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



class TraceConnectionsViewTest(APITestCase):
    def setUp(self):
        self.site_a = make_site('Site A')
        self.site_b = make_site('Site B')
        device_a = make_device(self.site_a, name='Router-A', serial='SN-001')
        device_b = make_device(self.site_b, name='Router-B', serial='SN-002')
        self.iface_a = make_interface(device_a, name='eth0')
        self.iface_b = make_interface(device_b, name='eth0')
        self.conn = make_connection(self.iface_a, self.iface_b, 'CONN-001')

    def _get(self, params):
        return self.client.get('/trace/', params)

    def test_trace_by_interface_returns_connection(self):
        response = self._get({'type': 'interface', 'id': self.iface_a.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [c['connection_id'] for c in response.data]
        self.assertIn('CONN-001', ids)

    def test_trace_by_device_returns_connection(self):
        response = self._get({'type': 'device', 'id': self.iface_a.device.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [c['connection_id'] for c in response.data]
        self.assertIn('CONN-001', ids)

    def test_trace_by_site_returns_connection(self):
        response = self._get({'type': 'site', 'id': self.site_a.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [c['connection_id'] for c in response.data]
        self.assertIn('CONN-001', ids)

    def test_trace_returns_empty_list_for_unconnected_element(self):
        isolated_site = make_site('Isolated Site')
        response = self._get({'type': 'site', 'id': isolated_site.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_missing_type_param_returns_400(self):
        response = self._get({'id': self.iface_a.pk})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_id_param_returns_400(self):
        response = self._get({'type': 'interface'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_type_returns_400(self):
        response = self._get({'type': 'network', 'id': 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_integer_id_returns_400(self):
        response = self._get({'type': 'interface', 'id': 'abc'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_interface_returns_404(self):
        response = self._get({'type': 'interface', 'id': 99999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_nonexistent_device_returns_404(self):
        response = self._get({'type': 'device', 'id': 99999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_nonexistent_site_returns_404(self):
        response = self._get({'type': 'site', 'id': 99999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_response_includes_nested_endpoint_detail(self):
        response = self._get({'type': 'interface', 'id': self.iface_a.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conn = response.data[0]
        self.assertIn('site', conn['start_target'])
        self.assertIn('device', conn['start_target'])
        self.assertIn('interface', conn['start_target'])
