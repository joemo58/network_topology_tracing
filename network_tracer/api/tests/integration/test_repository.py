from django.test import TestCase

from api.models import Connection, Device, Interface, Site
from api.repository import ElementNotFound, connections_for_device, connections_for_interface, connections_for_site


def make_site(name='Site A', status='AC'):
    return Site.objects.create(name=name, status=status)


def make_device(site, name='Router-1', serial='SN-001'):
    return Device.objects.create(name=name, site=site, serial_num=serial)


def make_interface(device, name='eth0', speed=1000, status='UP'):
    return Interface.objects.create(name=name, device=device, speed=speed, status=status)


def make_connection(start, end, conn_id='CONN-001', status='CON'):
    return Connection.objects.create(
        connection_id=conn_id, start_target=start, end_target=end, status=status
    )


class ConnectionsForInterfaceTest(TestCase):
    def setUp(self):
        site = make_site()
        device = make_device(site)
        self.iface_a = make_interface(device, name='eth0')
        self.iface_b = make_interface(device, name='eth1')
        self.iface_c = make_interface(device, name='eth2')
        self.conn_ab = make_connection(self.iface_a, self.iface_b, 'CONN-001')
        self.conn_bc = make_connection(self.iface_b, self.iface_c, 'CONN-002')

    def test_returns_connections_where_interface_is_start(self):
        result = connections_for_interface(self.iface_a.pk)
        self.assertIn(self.conn_ab, result)
        self.assertNotIn(self.conn_bc, result)

    def test_returns_connections_where_interface_is_end(self):
        result = connections_for_interface(self.iface_c.pk)
        self.assertIn(self.conn_bc, result)
        self.assertNotIn(self.conn_ab, result)

    def test_returns_both_connections_for_middle_interface(self):
        result = connections_for_interface(self.iface_b.pk)
        self.assertIn(self.conn_ab, result)
        self.assertIn(self.conn_bc, result)

    def test_returns_empty_queryset_for_unconnected_interface(self):
        result = connections_for_interface(self.iface_a.pk)
        # Remove the connection and recheck
        self.conn_ab.delete()
        result = connections_for_interface(self.iface_a.pk)
        self.assertEqual(result.count(), 0)

    def test_raises_element_not_found_for_missing_interface(self):
        with self.assertRaises(ElementNotFound):
            connections_for_interface(99999)


class ConnectionsForDeviceTest(TestCase):
    def setUp(self):
        site = make_site()
        self.device_a = make_device(site, name='Router-1', serial='SN-001')
        self.device_b = make_device(site, name='Router-2', serial='SN-002')
        self.device_c = make_device(site, name='Router-3', serial='SN-003')
        iface_a = make_interface(self.device_a, name='eth0')
        iface_b = make_interface(self.device_b, name='eth0')
        iface_c = make_interface(self.device_c, name='eth0')
        self.conn_ab = make_connection(iface_a, iface_b, 'CONN-001')
        self.conn_bc = make_connection(iface_b, iface_c, 'CONN-002')

    def test_returns_connections_where_device_has_start_interface(self):
        result = connections_for_device(self.device_a.pk)
        self.assertIn(self.conn_ab, result)
        self.assertNotIn(self.conn_bc, result)

    def test_returns_connections_where_device_has_end_interface(self):
        result = connections_for_device(self.device_c.pk)
        self.assertIn(self.conn_bc, result)
        self.assertNotIn(self.conn_ab, result)

    def test_returns_all_connections_for_middle_device(self):
        result = connections_for_device(self.device_b.pk)
        self.assertIn(self.conn_ab, result)
        self.assertIn(self.conn_bc, result)

    def test_returns_empty_queryset_for_device_with_no_connections(self):
        site = make_site('Site B')
        isolated_device = make_device(site, name='Isolated', serial='SN-999')
        result = connections_for_device(isolated_device.pk)
        self.assertEqual(result.count(), 0)

    def test_raises_element_not_found_for_missing_device(self):
        with self.assertRaises(ElementNotFound):
            connections_for_device(99999)


class ConnectionsForSiteTest(TestCase):
    def setUp(self):
        self.site_a = make_site('Site A')
        self.site_b = make_site('Site B')
        device_a = make_device(self.site_a, name='Router-A', serial='SN-001')
        device_b = make_device(self.site_b, name='Router-B', serial='SN-002')
        iface_a = make_interface(device_a, name='eth0')
        iface_b = make_interface(device_b, name='eth0')
        self.cross_site_conn = make_connection(iface_a, iface_b, 'CONN-001')

        device_a2 = make_device(self.site_a, name='Switch-A', serial='SN-003')
        iface_a2 = make_interface(device_a2, name='eth0')
        self.intra_site_conn = make_connection(iface_a, iface_a2, 'CONN-002')

    def test_returns_connection_where_site_has_start_device(self):
        result = connections_for_site(self.site_a.pk)
        self.assertIn(self.cross_site_conn, result)

    def test_returns_connection_where_site_has_end_device(self):
        result = connections_for_site(self.site_b.pk)
        self.assertIn(self.cross_site_conn, result)

    def test_returns_intra_site_connections(self):
        result = connections_for_site(self.site_a.pk)
        self.assertIn(self.intra_site_conn, result)

    def test_does_not_return_unrelated_site_connections(self):
        result = connections_for_site(self.site_b.pk)
        self.assertNotIn(self.intra_site_conn, result)

    def test_returns_empty_queryset_for_site_with_no_connections(self):
        empty_site = make_site('Empty Site')
        result = connections_for_site(empty_site.pk)
        self.assertEqual(result.count(), 0)

    def test_raises_element_not_found_for_missing_site(self):
        with self.assertRaises(ElementNotFound):
            connections_for_site(99999)
