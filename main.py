from vmware.mjolnir import fault_injection
from vmware.mjolnir.remote_machine_object import RemoteMachineObject

name = "107"
ip = '192.168.101.107'
username = "cmkldev"
password = "#2022%esx@CMKL"
ssh_port = 22

fault_type = "INFRA"
fault_sub_type = "CPU"
fault_payload="cpuLoad"


remote = [RemoteMachineObject(name = name, ip=ip, username= username, password = password, ssh_port = ssh_port)
]

fi = fault_injection.FaultInjection( remote, fault_type, fault_sub_type, fault_payload)






'''
Bug found

1.ConnectionRefusedError: [Errno 111] Connection refused

2.Failed to establish a new connection: [Errno 111] Connection refused'))

3.requests.exceptions.ConnectionError: HTTPSConnectionPool(host='192.168.101.180', port=443): Max retries exceeded 
with url: /mangle-services/rest/api/v1/endpoints/credentials 
(Caused by NewConnectionError('<urllib3.connection.HTTPSConnection object at 0x7fd2263728c0>: 
Failed to establish a new connection: [Errno 111] Connection refused'))

how to solve : 
method 1
https://stackoverflow.com/questions/23013220/max-retries-exceeded-with-url-in-requests


'''
