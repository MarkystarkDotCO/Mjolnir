from vmware.mjolnir import fault_injection
from vmware.mjolnir import fault_teardown
from vmware.mjolnir.remote_machine_object import RemoteMachineObject
from vmware.mjolnir.constants import Constants


const = Constants()
print("MANGLE_SERVER   :",const.MANGLE_SERVER)
print("MANGLE_USERNAME :",const.MANGLE_USERNAME)
print("MANGLE_PASSWORD :",const.MANGLE_PASSWORD)

rem = RemoteMachineObject

ft = fault_teardown.FaultTeardown()
#print(ft.wait_for_remediation_to_complete)
print(ft.remediate_all_faults)

fi = fault_injection.FaultInjection('','','')
print(fi.get_fault_type)


'''
example= [{
                        'name': '',
                        'ip': '',
                        'username': '',
                        'password': '',
                        'ssh_port': ''}]
'''
#remote = RemoteMachineObject(example)

#fi = fault_injection.FaultInjection( remote, 'fault_type', 'fault_sub_type', 'fault_payload')

#print(fi.add_remote_endpoint)
#print(fi.inject_fault)


#print('running OK')