"""
Copyright 2021 VMware, Inc. All rights reserved. -- VMware confidential
"""
import itertools

from vmware.mjolnir.constants import Constants as constants
from vmware.mjolnir.library.operations.endpoint_operations import \
    EndpointOperations, EndpointGroupOperations
from vmware.mjolnir.library.operations.fault_operations import \
    InfraFaultOperations
from vmware.mjolnir.library.operations.fault_operations import \
    AppFaultOperations
from vmware.mjolnir.library.api.restapi import RestApi

plugin_name = constants.PLUGIN_NAME


class FaultInjection(object):

    def __init__(self, remote_machine_objs, fault_type, fault_sub_type, fault_payload):
        self.endpoint_obj_lst = list()
        self.fault_type = fault_type
        self.fault_sub_type = fault_sub_type
        self.fault_payload = fault_payload
        self.endpoint_group = None
        self.task_id_list = list()

        # validate (up-front)
        # TODO

        # add remote endpoint
        self.add_remote_endpoint(remote_machine_objs)

        # inject_fault
        self.inject_fault(remote_machine_objs)

    @property
    def mangleapi(self):
        """
        will return, Mangle server object
        """
        return RestApi(constants.MANGLE_SERVER, constants.MANGLE_USERNAME,
                       constants.MANGLE_PASSWORD)

    def add_remote_endpoint(self, remote_machine_objs):
        """
        # TODO:
        :return:
        """
        mangle_api_obj = self.mangleapi
        for remote_machine_obj in remote_machine_objs:
            ep_oper = EndpointOperations(mangle_api_obj, remote_machine_obj)
            ep_oper.setup_fault_infra()
            self.endpoint_obj_lst.append(ep_oper)

        # if there is more than 1 endpoint of INFRA, then endpoint group is created
        # and then used for fault injection
        if len(remote_machine_objs) > 1 and self.fault_type == 'INFRA':
            self.endpoint_group = EndpointGroupOperations(
                mangle_api_obj, self.endpoint_obj_lst)
            self.endpoint_group.create_endpoint_group()

    def inject_fault(self, remote_machine_objs):
        """

        :return:
        """
        if self.endpoint_group and self.fault_type == 'INFRA':
            endpoint_obj = self.endpoint_group
        elif self.fault_type == 'APP':
            endpoint_obj = self.endpoint_obj_lst
        else:
            endpoint_obj = self.endpoint_obj_lst[0]

        # Infrastructure faults(s)
        if self.fault_type == "INFRA":
            infra_fault = InfraFaultOperations(endpoint_obj, remote_machine_objs)
            if self.fault_sub_type == "CPU":
                self.task_id_list = infra_fault.inject_fault(self.fault_sub_type,
                                                             cpuload=self.fault_payload[
                                                                 'cpuload'],
                                                             timeout=self.fault_payload[
                                                                 'timeout'])
            elif self.fault_sub_type == "MEMORY":
                self.task_id_list = infra_fault.inject_fault(self.fault_sub_type,
                                                             memoryload=self.fault_payload[
                                                                 'memoryload'],
                                                             timeout=self.fault_payload[
                                                                 'timeout'])
            elif self.fault_sub_type == "DISKIO":
                self.task_id_list = infra_fault.inject_fault(self.fault_sub_type,
                                                             iosize=self.fault_payload[
                                                                 'iosize'],
                                                             target_dir=self.fault_payload[
                                                                 'target_dir'],
                                                             timeout=self.fault_payload[
                                                                 'timeout'])
            elif self.fault_sub_type == "DISKSPACE":
                self.task_id_list = infra_fault.inject_fault(self.fault_sub_type,
                                                             diskload=self.fault_payload[
                                                                 'diskload'],
                                                             target_dir=self.fault_payload[
                                                                 'target_dir'],
                                                             timeout=self.fault_payload[
                                                                 'timeout'])
            elif self.fault_sub_type == "FILEHANDLERLEAK":
                self.task_id_list = infra_fault.inject_fault(self.fault_sub_type,
                                                             timeout=self.fault_payload[
                                                                 'timeout'])
            elif self.fault_sub_type == "KERNELPANIC":
                self.task_id_list = infra_fault.inject_fault(self.fault_sub_type,
                                                             timeout=self.fault_payload[
                                                                 'timeout'])
            elif self.fault_sub_type == "PROCESSKILL":
                self.task_id_list = infra_fault.inject_fault(self.fault_sub_type,
                                                             process_name=self.fault_payload.get(
                                                                 'process_descriptor', None),
                                                             process_id=self.fault_payload.get(
                                                                 'process_id', None))
            elif self.fault_sub_type == "STOPSVC":
                self.task_id_list = infra_fault.inject_fault(self.fault_sub_type,
                                                             svc_name=self.fault_payload.get(
                                                                 'svc_name'),
                                                             timeout=self.fault_payload.get(
                                                                 'timeout'))
            elif self.fault_sub_type == "CLOCKSKEW":
                self.task_id_list = infra_fault.inject_fault(self.fault_sub_type,
                                                             clockSkewOperation=self.fault_payload.get(
                                                                 'clock_skew_oper'),
                                                             seconds=self.fault_payload.get(
                                                                 'seconds', 0),
                                                             minutes=self.fault_payload.get(
                                                                 'minutes', 0),
                                                             hours=self.fault_payload.get(
                                                                 'hours', 0),
                                                             days=self.fault_payload.get('days',
                                                                                         0),
                                                             timeout=self.fault_payload.get(
                                                                 'timeout'))
            elif self.fault_sub_type == "NWPARTITION":
                self.task_id_list = infra_fault.inject_fault(self.fault_sub_type,
                                                             hosts=self.fault_payload.get(
                                                                 'hosts'),
                                                             timeout=self.fault_payload.get(
                                                                 'timeout'))
            elif self.fault_sub_type == "NETWORK":
                if self.fault_payload['nw_fault_type'] == "DELAY":
                    self.task_id_list = infra_fault.inject_fault(self.fault_sub_type,
                                                                 nw_fault_type=self.fault_payload[
                                                                     'nw_fault_type'],
                                                                 latency=self.fault_payload[
                                                                     'latency'],
                                                                 nicname=self.fault_payload[
                                                                     'nicname'],
                                                                 timeout=self.fault_payload[
                                                                     'timeout'])
                else:
                    self.task_id_list = infra_fault.inject_fault(self.fault_sub_type,
                                                                 nw_fault_type=self.fault_payload[
                                                                     'nw_fault_type'],
                                                                 percentage=self.fault_payload[
                                                                     'percentage'],
                                                                 nicname=self.fault_payload[
                                                                     'nicname'],
                                                                 timeout=self.fault_payload[
                                                                     'timeout'])

        # Application faults(s)
        if self.fault_type == "APP":
            for ep_obj, remote_machine_obj in zip(endpoint_obj, remote_machine_objs):
                app_fault = AppFaultOperations(ep_obj, remote_machine_obj)
                if self.fault_sub_type == "CPU":
                    self.task_id_list += app_fault.inject_fault(self.fault_sub_type,
                                                                cpuload=
                                                                self.fault_payload[
                                                                    'cpuload'],
                                                                timeout=
                                                                self.fault_payload[
                                                                    'timeout'],
                                                                java_home_path=
                                                                self.fault_payload[
                                                                    'java_home_path'],
                                                                jvm_process=
                                                                self.fault_payload[
                                                                    'jvm_process'],
                                                                user=
                                                                self.fault_payload[
                                                                    'user'],
                                                                free_port=self.fault_payload.get(
                                                                    'free_port',
                                                                    9091))
                if self.fault_sub_type == "MEMORY":
                    self.task_id_list += app_fault.inject_fault(self.fault_sub_type,
                                                                memoryload=
                                                                self.fault_payload[
                                                                    'memoryload'],
                                                                timeout=
                                                                self.fault_payload[
                                                                    'timeout'],
                                                                java_home_path=
                                                                self.fault_payload[
                                                                    'java_home_path'],
                                                                jvm_process=
                                                                self.fault_payload[
                                                                    'jvm_process'],
                                                                user=
                                                                self.fault_payload[
                                                                    'user'],
                                                                free_port=self.fault_payload.get(
                                                                    'free_port',
                                                                    9091))

                if self.fault_sub_type == "FILEHANDLERLEAK":
                    self.task_id_list += app_fault.inject_fault(self.fault_sub_type,
                                                                timeout=
                                                                self.fault_payload[
                                                                    'timeout'],
                                                                java_home_path=
                                                                self.fault_payload[
                                                                    'java_home_path'],
                                                                jvm_process=
                                                                self.fault_payload[
                                                                    'jvm_process'],
                                                                user=
                                                                self.fault_payload[
                                                                    'user'],
                                                                free_port=self.fault_payload.get(
                                                                    'free_port',
                                                                    9091))
                if self.fault_sub_type == "THREADLEAK":
                    self.task_id_list += app_fault.inject_fault(self.fault_sub_type,
                                                                timeout=
                                                                self.fault_payload[
                                                                    'timeout'],
                                                                java_home_path=
                                                                self.fault_payload[
                                                                    'java_home_path'],
                                                                jvm_process=
                                                                self.fault_payload[
                                                                    'jvm_process'],
                                                                user=
                                                                self.fault_payload[
                                                                    'user'],
                                                                oom_req=self.fault_payload.get(
                                                                    'oom_req',
                                                                    True),
                                                                free_port=self.fault_payload.get(
                                                                    'free_port',
                                                                    9091))
