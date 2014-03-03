
from libcloud.compute.drivers import ec2, openstack

ec2.API_VERSION = "2013-10-15"

ec2.EC2NodeDriver.create_node_kwargs = [
    'ex_securitygroup',
    'ex_keyname',
    'ex_userdata',
    'ex_clienttoken',
    'ex_blockdevicemappings',
    'ex_iamprofile',
]


openstack.OpenStackNodeDriver.kwargs = [
    'key',
    'secret',
    'ex_force_base_url',
    'ex_force_auth_url',
    'ex_force_auth_version',
    'ex_force_auth_token',
    'ex_tenant_name',
    'ex_force_service_type',
    'ex_force_service_name',
    'ex_force_service_region',
    ]
