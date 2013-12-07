
from libcloud.compute.drivers import ec2

ec2.API_VERSION = "2013-10-15"

ec2.EC2NodeDriver.create_node_kwargs = [
    'ex_securitygroup',
    'ex_keyname',
    'ex_userdata',
    'ex_clienttoken',
    'ex_blockdevicemappings',
    'ex_iamprofile',
]
