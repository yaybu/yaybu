
from libcloud.compute.drivers.ec2 import EC2NodeDriver

EC2NodeDriver.create_node_kwargs = [
    'ex_securitygroup',
    'ex_keyname',
    'ex_userdata',
    'ex_clienttoken',
    'ex_blockdevicemappings',
    ]

