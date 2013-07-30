
from libcloud.compute.drivers.ec2 import EC2NodeDriver

EC2NodeDriver.create_node_kwargs = [
    'ex_securitygroup',
    'ex_keyname',
    'ex_userdata',
    'ex_clienttoken',
    'ex_blockdevicemappings',
    ]

# see https://issues.apache.org/jira/browse/LIBCLOUD-367
EC2NodeDriver.features['create_node'] = []

