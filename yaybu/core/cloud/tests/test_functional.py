
#from yaybu.core.cloud import api
#from yaybu.core.command import YaybuCmd
#from libcloud.compute.providers import Provider as ComputeProvider
#from libcloud.storage.providers import Provider as StorageProvider
#from libcloud.dns.providers import Provider as DNSProvider

#from libcloud.compute import providers as compute_providers
#from libcloud.storage import providers as storage_providers
#from libcloud.dns import providers as dns_providers

#from mock import MagicMock as Mock
#import tempfile
#import unittest

#class DummyComputeProvider(ComputeProvider):
    #YAYBUDUMMY = -1
    
#class DummyStorageProvider(StorageProvider):
    #YAYBUDUMMY = -1
    
#class DummyDNSProvider(DNSProvider):
    #YAYBUDUMMY = -1
    
##api.ComputeProvider = DummyComputeProvider
##api.StorageProvider = DummyStorageProvider
##api.DNSProvider = DummyDNSProvider

##compute_providers.DRIVERS[DummyComputeProvider.YAYBUDUMMY] = ('yaybu.core.cloud.tests.dummy', 'DummyComputeDriver')
##storage_providers.DRIVERS[DummyStorageProvider.YAYBUDUMMY] = ('yaybu.core.cloud.tests.dummy', 'DummyStorageDriver')
##dns_providers.DRIVERS[DummyDNSProvider.YAYBUDUMMY] = ('yaybu.core.cloud.tests.dummy', 'DummyDNSDriver')


#test_commands = """
#clouds:
    #fake_cloud:
        #providers: 
            #compute: YAYBUDUMMY
            #storage: YAYBUDUMMY
            #dns: YAYBUDUMMY
        #compute_args:
            #creds: 5
        #storage_args:
            #api_key: x
            #api_secret: x
        #images:
            #FAKE_IMAGE_NAME: 1
        #sizes:
            #small: 1
            #medium: 2
            #big: 3
        #keys:
            #FAKE_KEY: package://yaybu/core/cloud/tests/test_keys.pem
            
#roles:
    #foo:
        #key: FAKE_KEY
        #instance:
            #image: FAKE_IMAGE_NAME
            #size: medium
        #include:
            #package://yaybu/core/cloud/tests/commands_foo.yay
        #max: 1
        #min: 1
        #dns:
            #zone: example.com
            #name: foo
    #bar:
        #key: FAKE_KEY
        #instance:
            #image: FAKE_IMAGE_NAME
            #size: medium
        #include:
            #package://yaybu/core/cloud/tests/commands_bar.yay
        #max: 1
        #min: 1
        #dns:
            #zone: example.com
            #name: foo
        
#"""

##class TestFunctional(unittest.TestCase):
    
    ##def test_provision(self):
        
        ##cmd = YaybuCmd()
        ##tmp = tempfile.NamedTemporaryFile(delete=False)
        ##tmp.write(test_commands)
        ##tmp.close()
        ##cmd.do_provision({}, ["fake_cloud", "fake_cluster", tmp.name])
        
        