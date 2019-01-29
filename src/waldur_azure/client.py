import sys
import six

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import DiskCreateOption
from azure.mgmt.compute.compute.models import LinuxConfiguration, OSProfile, SshConfiguration, SshPublicKey
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.rdbms.postgresql import PostgreSQLManagementClient
from azure.mgmt.rdbms.postgresql.models import ServerForCreate, ServerPropertiesForDefaultCreate, ServerVersion
from azure.mgmt.storage import StorageManagementClient
from django.utils.functional import cached_property
from msrestazure.azure_exceptions import CloudError

from waldur_core.structure import ServiceBackendError


class AzureBackendError(ServiceBackendError):
    pass


def reraise(exc):
    """
    Reraise AzureBackendError while maintaining traceback.
    """
    six.reraise(AzureBackendError, exc, sys.exc_info()[2])


class AzureClient(object):
    def __init__(self, settings):
        self.subscription_id = str(settings.options['subscription_id'])
        self.client_id = str(settings.options['client_id'])
        self.client_secret = str(settings.options['client_secret'])
        self.tenant_id = str(settings.options['tenant_id'])

    @cached_property
    def credentials(self):
        return ServicePrincipalCredentials(
            client_id=self.client_id,
            secret=self.client_secret,
            tenant=self.tenant_id,
        )

    @cached_property
    def subscription_client(self):
        return SubscriptionClient(self.credentials)

    @cached_property
    def resource_client(self):
        return ResourceManagementClient(self.credentials, self.subscription_id)

    @cached_property
    def compute_client(self):
        return ComputeManagementClient(self.credentials, self.subscription_id)

    @cached_property
    def storage_client(self):
        return StorageManagementClient(self.credentials, self.subscription_id)

    @cached_property
    def network_client(self):
        return NetworkManagementClient(self.credentials, self.subscription_id)

    @cached_property
    def pgsql_client(self):
        return PostgreSQLManagementClient(self.credentials, self.subscription_id)

    def list_locations(self):
        try:
            return self.subscription_client.subscriptions.list_locations(self.subscription_id)
        except CloudError as e:
            reraise(e)

    def list_resource_groups(self):
        try:
            return self.resource_client.resource_groups.list()
        except CloudError as e:
            reraise(e)

    def create_resource_group(self, location, resource_group_name):
        try:
            return self.resource_client.resource_groups.create_or_update(
                resource_group_name,
                {'location': location}
            )
        except CloudError as e:
            reraise(e)

    def delete_resource_group(self, resource_group_name):
        try:
            return self.resource_client.resource_groups.delete(resource_group_name)
        except CloudError as e:
            reraise(e)

    def list_virtual_machine_sizes(self, location):
        try:
            return self.compute_client.virtual_machine_sizes.list(location)
        except CloudError as e:
            reraise(e)

    def list_virtual_machine_images(self, location):
        try:
            publishers = self.compute_client.virtual_machine_images.list_publishers(location)

            for publisher in publishers:
                offers = self.compute_client.virtual_machine_images.list_offers(
                    location,
                    publisher.name,
                )

                for offer in offers:
                    skus = self.compute_client.virtual_machine_images.list_skus(
                        location,
                        publisher.name,
                        offer.name,
                    )

                    for sku in skus:
                        result_list = self.compute_client.virtual_machine_images.list(
                            location,
                            publisher.name,
                            offer.name,
                            sku.name,
                        )

                        for version in result_list:
                            yield self.compute_client.virtual_machine_images.get(
                                location,
                                publisher.name,
                                offer.name,
                                sku.name,
                                version.name,
                            )
        except CloudError as e:
            reraise(e)

    def list_all_virtual_machines(self):
        try:
            return self.compute_client.virtual_machines.list_all()
        except CloudError as e:
            reraise(e)

    def list_virtual_machines_in_group(self, resource_group_name):
        try:
            return self.compute_client.virtual_machines.list(resource_group_name)
        except CloudError as e:
            reraise(e)

    def get_virtual_machine(self, resource_group_name, vm_name):
        try:
            return self.compute_client.virtual_machines.get(
                resource_group_name,
                vm_name
            )
        except CloudError as e:
            reraise(e)

    def create_virtual_machine(self, location, resource_group_name,
                               vm_name, size_name, nic_id, image_reference,
                               username, password, custom_data=None, ssh_key=None):
        os_profile = OSProfile(
            computer_name=vm_name,
            admin_username=username,
            admin_password=password,
        )
        if custom_data:
            os_profile.custom_data = custom_data

        if ssh_key:
            os_profile.linux_configuration = LinuxConfiguration(
                ssh=SshConfiguration(
                    public_keys=[
                        SshPublicKey(key_data=ssh_key),
                    ],
                )
            )
        try:
            return self.compute_client.virtual_machines.create_or_update(
                resource_group_name,
                vm_name,
                {
                    'location': location,
                    'os_profile': os_profile,
                    'hardware_profile': {
                        'vm_size': size_name,
                    },
                    'storage_profile': {
                        'image_reference': image_reference,
                    },
                    'network_profile': {
                        'network_interfaces': [{
                            'id': nic_id,
                        }]
                    },
                },
            )
        except CloudError as e:
            reraise(e)

    def delete_virtual_machine(self, resource_group_name, vm_name):
        try:
            return self.compute_client.virtual_machines.delete(
                resource_group_name,
                vm_name,
            )
        except CloudError as e:
            reraise(e)

    def start_virtual_machine(self, resource_group_name, vm_name):
        try:
            return self.compute_client.virtual_machines.start(
                resource_group_name,
                vm_name,
            )
        except CloudError as e:
            reraise(e)

    def restart_virtual_machine(self, resource_group_name, vm_name):
        try:
            return self.compute_client.virtual_machines.restart(
                resource_group_name,
                vm_name,
            )
        except CloudError as e:
            reraise(e)

    def stop_virtual_machine(self, resource_group_name, vm_name):
        try:
            return self.compute_client.virtual_machines.power_off(
                resource_group_name,
                vm_name,
            )
        except CloudError as e:
            reraise(e)

    def create_storage_account(self, location, resource_group_name, account_name):
        try:
            return self.storage_client.storage_accounts.create(
                resource_group_name,
                account_name,
                {
                    'sku': {'name': 'standard_lrs'},
                    'kind': 'storage',
                    'location': location
                }
            )
        except CloudError as e:
            reraise(e)

    def create_disk(self, location, resource_group_name, disk_name, disk_size_gb):
        try:
            return self.compute_client.disks.create_or_update(
                resource_group_name,
                disk_name,
                {
                    'location': location,
                    'disk_size_gb': disk_size_gb,
                    'creation_data': {
                        'create_option': DiskCreateOption.empty
                    }
                }
            )
        except CloudError as e:
            reraise(e)

    def create_network(self, location, resource_group_name, network_name, cidr):
        try:
            return self.network_client.virtual_networks.create_or_update(
                resource_group_name,
                network_name,
                {
                    'location': location,
                    'address_space': {
                        'address_prefixes': [cidr]
                    }
                }
            )
        except CloudError as e:
            reraise(e)

    def create_subnet(self, resource_group_name, network_name, subnet_name, cidr):
        try:
            return self.network_client.subnets.create_or_update(
                resource_group_name,
                network_name,
                subnet_name,
                {
                    'address_prefix': cidr,
                }
            )
        except CloudError as e:
            reraise(e)

    def create_network_interface(self, location, resource_group_name,
                                 interface_name, config_name, subnet_id):
        try:
            return self.network_client.network_interfaces.create_or_update(
                resource_group_name,
                interface_name,
                {
                    'location': location,
                    'ip_configurations': [{
                        'name': config_name,
                        'subnet': {
                            'id': subnet_id,
                        }
                    }]
                }
            )
        except CloudError as e:
            reraise(e)

    def list_all_sql_servers(self):
        try:
            return self.pgsql_client.servers.list()
        except CloudError as e:
            reraise(e)

    def list_sql_servers_in_group(self, resource_group_name):
        try:
            return self.pgsql_client.servers.list_by_resource_group(resource_group_name)
        except CloudError as e:
            reraise(e)

    def get_sql_server(self, resource_group_name, server_name):
        try:
            return self.pgsql_client.servers.get_by_resource_group(
                resource_group_name,
                server_name,
            )
        except CloudError as e:
            reraise(e)

    def create_sql_server(self, location, resource_group_name, server_name,
                          username, password, sku=None, storage_mb=None, ssl_enforcement=None):
        try:
            return self.pgsql_client.servers.create_or_update(
                resource_group_name,
                server_name,
                ServerForCreate(
                    ServerPropertiesForDefaultCreate(
                        administrator_login=username,
                        administrator_login_password=password,
                        version=ServerVersion.nine_full_stop_six,
                        storage_mb=storage_mb,
                        ssl_enforcement=ssl_enforcement,
                    ),
                    location=location,
                    sku=sku,
                )
            )
        except CloudError as e:
            reraise(e)

    def delete_sql_server(self, resource_group_name, server_name):
        try:
            return self.pgsql_client.servers.delete(resource_group_name, server_name)
        except CloudError as e:
            reraise(e)

    def create_sql_firewall_rule(self, resource_group_name, server_name, firewall_rule_name,
                                 start_ip_address, end_ip_address):
        try:
            return self.pgsql_client.firewall_rules.create_or_update(
                resource_group_name,
                server_name,
                firewall_rule_name,
                start_ip_address,
                end_ip_address,
            )
        except CloudError as e:
            reraise(e)

    def get_sql_database(self, resource_group_name, server_name, database_name):
        try:
            return self.pgsql_client.databases.get(
                resource_group_name,
                server_name,
                database_name,
            )
        except CloudError as e:
            reraise(e)

    def create_sql_database(self, location, resource_group_name, server_name, database_name):
        try:
            return self.pgsql_client.databases.create_or_update(
                resource_group_name,
                server_name,
                database_name,
                {
                    'location': location
                }
            )
        except CloudError as e:
            reraise(e)

    def list_sql_databases_in_server(self, resource_group_name, server_name):
        try:
            return self.pgsql_client.databases.list_by_server(
                resource_group_name,
                server_name,
            )
        except CloudError as e:
            reraise(e)

    def delete_sql_database(self, resource_group_name, server_name, database_name):
        try:
            return self.pgsql_client.databases.delete(
                resource_group_name,
                server_name,
                database_name,
            )
        except CloudError as e:
            reraise(e)
