from asyncio import constants
from unicodedata import name
from vmware.mjolnir import fault_injection
from vmware.mjolnir import fault_teardown
from vmware.mjolnir.infrastructure import ssh_server
from vmware.mjolnir.library.api import restapi 
from vmware.mjolnir.remote_machine_object import RemoteMachineObject


ft = fault_teardown.FaultTeardown
print(ft.wait_for_remediation_to_complete)
print(ft.remediate_all_faults)



example= [{
                        'name': '',
                        'ip': '',
                        'username': '',
                        'password': '',
                        'ssh_port': ''}]

remote = RemoteMachineObject(example)

fi = fault_injection.FaultInjection( remote, 'fault_type', 'fault_sub_type', 'fault_payload')

print(fi.add_remote_endpoint)
print(fi.inject_fault)


#print('running OK')