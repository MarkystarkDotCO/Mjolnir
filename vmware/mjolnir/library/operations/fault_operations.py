"""
Copyright 2021 VMware, Inc. All rights reserved. -- VMware confidential
"""

import json
import logging

from vmware.mjolnir.constants import Constants as constants
from collections import OrderedDict
from vmware.mjolnir.infrastructure import utilities
from vmware.mjolnir.library.api.faults import Faults
from vmware.mjolnir.library.api.restapi import RestApi
from vmware.mjolnir.infrastructure.ssh_server import SshServer
from vmware.mjolnir.library.operations.common_operations import CommonOps
from vmware.mjolnir.library.operations.task_operations import TaskOperations
from vmware.mjolnir.library.operations.endpoint_operations import EndpointGroupOperations

log = logging.getLogger(__name__)
plugin_name = constants.PLUGIN_NAME


class FaultBase(object):
    """
    Fault Operations for API Library
    """
    # Creating separate ordered dict for INFRA fault operation
    infra_faultops_dict = OrderedDict()
    infra_faultops_dict['CPU'] = 'generate_cpu_fault'
    infra_faultops_dict['MEMORY'] = 'generate_memory_fault'
    infra_faultops_dict['DISKIO'] = 'generate_diskio_fault'
    infra_faultops_dict['PROCESSKILL'] = 'generate_processkill_fault'
    infra_faultops_dict['STOPSVC'] = 'generate_stop_service_fault'
    infra_faultops_dict['FILEHANDLERLEAK'] = 'generate_file_handler_leak_fault'
    infra_faultops_dict['KERNELPANIC'] = 'generate_kernel_panic_fault'
    infra_faultops_dict['DISKSPACE'] = 'generate_diskspace_fault'
    infra_faultops_dict['NETWORK'] = 'generate_network_fault'
    infra_faultops_dict['CLOCKSKEW'] = 'generate_clockskew_fault'
    infra_faultops_dict['NWPARTITION'] = 'generate_nw_partition_fault'

    # Creating separate ordered dict for APP fault operations
    app_faultops_dict = OrderedDict()
    app_faultops_dict['CPU'] = 'generate_cpu_fault'
    app_faultops_dict['MEMORY'] = 'generate_memory_fault'
    app_faultops_dict['FILEHANDLERLEAK'] = 'generate_file_handler_leak_fault'
    app_faultops_dict['THREADLEAK'] = 'generate_thread_leak_fault'

    # Creating a common ordered dict for fault operations which will have both INFRA and APP ordered dicts
    faultops_dict = OrderedDict()
    faultops_dict['INFRA'] = infra_faultops_dict
    faultops_dict['APP'] = app_faultops_dict

    network_fault_map = {'DELAY': 'NETWORK_DELAY_MILLISECONDS',
                         'DUPLICATE': 'PACKET_DUPLICATE_PERCENTAGE',
                         'CORRUPT': 'PACKET_CORRUPT_PERCENTAGE',
                         'LOSS': 'PACKET_LOSS_PERCENTAGE'
                         }

    def __init__(self, mangle_ip, mangle_username, mangle_password, endpoint,
                 fault_area, remote_machine_objs):

        self.mangle_ip = mangle_ip
        self.mangle_username = mangle_username
        self.mangle_password = mangle_password

        # Initialize endpoints
        self.endpoint = endpoint

        # Initialize fault area i.e INFRA or APP
        self.fault_area = fault_area

        for remote_machine_obj in remote_machine_objs:
            # create ssh connection object
            self.ssh_server = SshServer(remote_machine_obj.ip,
                                        remote_machine_obj.username,
                                        remote_machine_obj.password,
                                        remote_machine_obj.ssh_port)
            self.ssh_server.connect()

            # fix as per: https://bugzilla.eng.vmware.com/show_bug.cgi?id=2365947
            result, err, out = self.ssh_server.ssh(constants.CMD_REMOUNT_TEMP, timeout=120)
            log.info("%s *** [node:port %s:%s] remounted /tmp ***:: %s",
                     plugin_name, remote_machine_obj.ip,
                     remote_machine_obj.ssh_port, result)
            self.ssh_server.close()


        self.remote_machine_obj = remote_machine_objs[0]
        self.ssh_server = SshServer(self.remote_machine_obj.ip,
                                    self.remote_machine_obj.username,
                                    self.remote_machine_obj.password,
                                    self.remote_machine_obj.ssh_port)
        self.ssh_server.connect()

    @property
    def mangleapi(self):
        """
        # TODO:
        """
        return RestApi(self.mangle_ip, self.mangle_username,
                       self.mangle_password)

    def inject_fault(self, fault_type, **kwargs):
        """
        # TODO:
        """
        method = self.faultops_dict[self.fault_area][fault_type]
        return getattr(self, method)(**kwargs)

    def invoke_mangle_api(self, payload, fault_area, fault_type):
        """
        # TODO:
        """
        # log the fault injection
        FaultBase._log_fault(fault_area, fault_type, payload)

        faults_obj = Faults(self.mangleapi)
        result, err, out = self.ssh_server.ssh(constants.CMD_DATE, timeout=120)
        log.info("%s *** [node: %s] time to inject fault ***:: %s",
                 plugin_name, self.remote_machine_obj.ip, result.strip())

        ret_val, content = faults_obj.inject(fault_type, json.dumps(payload))
        if "id" not in content.keys():
            raise RuntimeError(
                "{} *** Fault {}:{} injection failed***:: {}".format(
                    plugin_name, fault_area, fault_type, str(content)))

        if isinstance(self.endpoint, EndpointGroupOperations):
            task_details = CommonOps.get_task_details(self.mangleapi,
                                                      task_id=content['id'])
            child_tasks = task_details['triggers'][0]['childTaskIDs']
            CommonOps.poll_fault_status(self.mangleapi, fault_id=content['id'],
                                        expected_status=["INJECTED", "COMPLETED"])
            log.info("%s *** Polling for each child task :: %s ", plugin_name, child_tasks)
            # wait for child faults to get injected
            for task in child_tasks:
                CommonOps.poll_fault_status(self.mangleapi, fault_id=task)
            # log the successful completion of fault
            FaultBase._log_fault(fault_area, fault_type, payload, success_msg=1)
            return child_tasks
        else:
            # wait for fault to get injected
            CommonOps.poll_fault_status(self.mangleapi, fault_id=content['id'],
                                        expected_status=["INJECTED", "COMPLETED"])
            FaultBase._log_fault(fault_area, fault_type, payload, success_msg=1)
            return [content['id']]


    @staticmethod
    def _get_json_obj(fname):
        """
        # TODO:
        """
        try:
            with open(fname) as json_file:
                return json.load(json_file)
        except json.decoder.JSONDecodeError as jerr:
            raise Exception("Invalid JSON in body: %s", jerr)

    def get_process_id(self, process_name, process_uname):
        """
        # TODO:
        """
        # username = process_uname
        process_identifier = {
            # identifiers to identify:
            "corfu": "corfu_oom",
            "corfu-nonconfig": "corfu-nonconfig_oom",
            "cbm": "cbm_oom",
            "proton": "proton_oom",
            "policy": "policy_oom"
        }

        if process_name not in ['corfu', 'corfu-nonconfig', 'cbm', 'proton',
                                 'policy']:
            log.debug(
                    "%s supported process are: ['corfu', 'corfu-nonconfig', 'cbm', 'proton', 'policy']",
                    plugin_name)
            raise ValueError("unsupported process: %s", process_name)

        # build command
        cmd = "pgrep -u %s -la|grep '%s'|awk '{print $1}'" % \
              (process_uname, process_identifier[process_name])

        log.debug("%s *** running command: %s on node %s ***",
                  plugin_name, cmd, self.endpoint.ep_ip)
        result, err, out = self.ssh_server.ssh(cmd, timeout=120)
        pid = int(result.strip())
        log.debug("%s *** pid is %s ***", plugin_name, pid)
        return pid

    @staticmethod
    def set_schedule(schedule_epoch_time, schedule_cron_exp):
        """
        # TODO:
        """
        schedule = {}
        if schedule_cron_exp is not None and schedule_epoch_time is not None:
            raise Exception("%s *** either provide schedule_cron_exp"
                            " or schedule_epoch_time", plugin_name)
        elif schedule_cron_exp is None and schedule_epoch_time is None:
            return schedule
        elif schedule_cron_exp is None:
            schedule["timeoutInMilliseconds"] = schedule_epoch_time
        elif schedule_epoch_time is None:
            schedule["cronExpression"] = schedule_cron_exp

        return schedule

    @staticmethod
    def verify_kill_argument(process_name, process_id):
        """
        # TODO:
        """

        if process_name is not None and process_id is not None and \
                process_name is None and process_id is None:
            raise Exception("%s ** either provide process_name or process_id **",
                            plugin_name)
        elif process_name is None:
            return process_id
        elif process_id is None:
            return process_name

    @staticmethod
    def _log_fault(fault_area, fault_type, payload, success_msg=0):
        """
        # TODO
        """

        if success_msg:
            log.debug("%s *** %s::%s FAULT INJECTED SUCCESSFULLY ***",
                      plugin_name, fault_area, fault_type)
            log.debug("%s *** %s::%s FAULT INJECTED SUCCESSFULLY ***",
                      plugin_name, fault_area, fault_type)
        else:
            log.debug("%s *** GENERATING %s::%s ***", plugin_name,
                      fault_area, fault_type)
            log.debug("%s *** PAYLOAD FOR %s::%s *** \n %s", plugin_name,
                      fault_area, fault_type, payload)


class InfraFaultOperations(FaultBase):
    """
    # TODO:
    """

    def __init__(self, end_point, remote_machine_objs, fault_area="INFRA"):

        # mangle server detail(s)
        # self.mangle_ip = constants.MANGLE_SERVER_LIST[random.randint(0, 2)]

        FaultBase.__init__(self, constants.MANGLE_SERVER,
                           constants.MANGLE_USERNAME, constants.MANGLE_PASSWORD,
                           end_point, fault_area, remote_machine_objs)

    def generate_cpu_fault(self, cpuload, timeout, injection_homedir="/tmp",
                           schedule_epoch_time=None, schedule_cron_exp=None,
                           tags={}):
        """
        # TODO
        """
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict['INFRA'].keys())[0]

        schedule = FaultBase.set_schedule(schedule_epoch_time,
                                          schedule_cron_exp)
        payload = {
            "cpuLoad": cpuload,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.endpoint.ep_name,
            "randomEndpoint": False,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags
        }

        return self.invoke_mangle_api(payload, fault_area, fault_type)

    def generate_memory_fault(
            self, memoryload, timeout, injection_homedir="/tmp",
            schedule_epoch_time=None, schedule_cron_exp=None, tags={}):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict['INFRA'].keys())[1]

        schedule = FaultBase.set_schedule(schedule_epoch_time,
                                          schedule_cron_exp)
        payload = {
            "memoryLoad": memoryload,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.endpoint.ep_name,
            "randomEndpoint": False,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags
        }

        return self.invoke_mangle_api(payload, fault_area, fault_type)

    def generate_diskio_fault(self, iosize, target_dir, timeout,
                              injection_homedir="/tmp",
                              schedule_epoch_time=None, schedule_cron_exp=None,
                              tags={}):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict['INFRA'].keys())[2]

        schedule = FaultBase.set_schedule(schedule_epoch_time,
                                          schedule_cron_exp)
        payload = {
            "ioSize": iosize,
            "targetDir": target_dir,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.endpoint.ep_name,
            "randomEndpoint": False,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags
        }

        return self.invoke_mangle_api(payload, fault_area, fault_type)

    def generate_processkill_fault(self, process_name=None, process_id=None,
                                   remediation_cmd=None,
                                   injection_homedir="/tmp",
                                   schedule_epoch_time=None,
                                   schedule_cron_exp=None, tags={}):
        """
        # TODO:
        """

        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict['INFRA'].keys())[3]

        schedule = FaultBase.set_schedule(schedule_epoch_time,
                                          schedule_cron_exp)
        kill_all = None
        payload = {
            "injectionHomeDir": injection_homedir,
            "remediationCommand": remediation_cmd,
            "endpointName": self.endpoint.ep_name,
            "randomEndpoint": False,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags
        }

        # verify kill argument
        kill_arg = FaultBase.verify_kill_argument(process_name, process_id)

        if isinstance(kill_arg, str):
            kill_all = True
            payload['processIdentifier'] = process_name
            payload['killAll'] = kill_all
        if isinstance(kill_arg, int):
            kill_all = False
            payload['processId'] = process_id
            payload['killAll'] = kill_all

        return self.invoke_mangle_api(payload, fault_area, fault_type)

    def generate_stop_service_fault(self, svc_name, timeout, injection_homedir="/tmp",
                                    schedule_epoch_time=None,
                                    schedule_cron_exp=None, tags={}):
        """
        # TODO:
        """

        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict['INFRA'].keys())[4]

        schedule = FaultBase.set_schedule(schedule_epoch_time,
                                          schedule_cron_exp)
        payload = {
            "injectionHomeDir": injection_homedir,
            "timeoutInMilliseconds": timeout * 1000,
            "serviceName": svc_name,
            "endpointName": self.endpoint.ep_name,
            "randomEndpoint": False,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags
        }

        return self.invoke_mangle_api(payload, fault_area, fault_type)

    def generate_file_handler_leak_fault(self, timeout,
                                         injection_homedir="/tmp",
                                         schedule_epoch_time=None,
                                         schedule_cron_exp=None, tags={}):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict['INFRA'].keys())[5]

        schedule = FaultBase.set_schedule(schedule_epoch_time,
                                          schedule_cron_exp)
        payload = {
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.endpoint.ep_name,
            "randomEndpoint": False,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags
        }

        return self.invoke_mangle_api(payload, fault_area, fault_type)

    def generate_kernel_panic_fault(self, timeout, injection_homedir="/tmp",
                                    schedule_epoch_time=None,
                                    schedule_cron_exp=None, tags={}):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict['INFRA'].keys())[6]

        schedule = FaultBase.set_schedule(schedule_epoch_time,
                                          schedule_cron_exp)
        payload = {
            "injectionHomeDir": injection_homedir,
            "endpointName": self.endpoint.ep_name,
            "timeoutInMilliseconds": timeout * 1000,
            "randomEndpoint": False,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags
        }

        return self.invoke_mangle_api(payload, fault_area, fault_type)

    def generate_diskspace_fault(self, diskload, target_dir, timeout,
                                 injection_homedir="/tmp", schedule_epoch_time=None,
                                 schedule_cron_exp=None, tags={}):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict['INFRA'].keys())[7]

        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)
        payload = {
            "diskFillSize": diskload,
            "directoryPath": target_dir,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.endpoint.ep_name,
            "randomEndpoint": False,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags
        }
        return self.invoke_mangle_api(payload, fault_area, fault_type)

    def generate_network_fault(self, nw_fault_type, nicname, timeout, injection_homedir="/tmp",
                               latency=None, percentage=None, schedule_epoch_time=None,
                               schedule_cron_exp=None, tags={}):
        """
        # TODO:
        """
        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict['INFRA'].keys())[8]

        if nw_fault_type == 'DELAY' and latency is None:
            raise Exception("%s latency parameter is None for Network delay fault",
                            plugin_name)
        elif nw_fault_type != 'DELAY' and percentage is None:
            raise Exception("%s percentage parameter is None for Network fault",
                            plugin_name)

        payload = {
            "faultOperation": self.network_fault_map[nw_fault_type],
            "nicName": nicname,
            "latency": latency,
            "percentage": percentage,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.endpoint.ep_name,
            "randomEndpoint": False,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags
        }

        return self.invoke_mangle_api(payload, fault_area, fault_type)

    def generate_clockskew_fault(self, clockSkewOperation, days, hours,
                                 minutes, seconds, timeout,
                                 injection_homedir="/tmp",
                                 schedule_epoch_time=None,
                                 schedule_cron_exp=None, tags={}):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict['INFRA'].keys())[9]

        schedule = FaultBase.set_schedule(schedule_epoch_time,
                                          schedule_cron_exp)
        payload = {
            "clockSkewOperation": clockSkewOperation,
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.endpoint.ep_name,
            "randomEndpoint": False,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags
        }
        return self.invoke_mangle_api(payload, fault_area, fault_type)

    def generate_nw_partition_fault(self, hosts, timeout, injection_homedir="/tmp",
                                    schedule_epoch_time=None,
                                    schedule_cron_exp=None, tags={}):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[0]
        fault_type = list(self.faultops_dict['INFRA'].keys())[10]

        schedule = FaultBase.set_schedule(schedule_epoch_time,
                                          schedule_cron_exp)
        payload = {
            "hosts": hosts,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.endpoint.ep_name,
            "randomEndpoint": False,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags
        }
        return self.invoke_mangle_api(payload, fault_area, fault_type)


class AppFaultOperations(FaultBase):
    """
    # TODO:
    """

    def __init__(self, end_point, remote_machine_obj, fault_area="APP"):

        # TODO: optimized get constants for APPS & INFRA (remove duplicate code)
        FaultBase.__init__(self, constants.MANGLE_SERVER,
                           constants.MANGLE_USERNAME, constants.MANGLE_PASSWORD,
                           end_point, fault_area, remote_machine_obj)

    def generate_cpu_fault(self, cpuload, timeout, java_home_path, jvm_process,
                           user, free_port, injection_homedir="/tmp",
                           schedule_epoch_time=None, schedule_cron_exp=None,
                           tags={}):
        """
        # TODO:
        """

        fault_area = list(self.faultops_dict.keys())[1]
        fault_type = list(self.faultops_dict['APP'].keys())[0]

        schedule = FaultBase.set_schedule(schedule_epoch_time,
                                          schedule_cron_exp)
        # if 'jvm_process' name is passed, get pid of process
        if isinstance(jvm_process, str):
            jvm_process = self.get_process_id(jvm_process, process_uname=user)

        payload = {
            "cpuLoad": cpuload,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.endpoint.ep_name,
            "randomEndpoint": False,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
            "jvmProperties": {"javaHomePath": java_home_path,
                              "jvmprocess": jvm_process, "user": user,
                              "port": free_port}
        }

        return self.invoke_mangle_api(payload, fault_area, fault_type)

    def generate_memory_fault(
            self, memoryload, timeout, java_home_path, jvm_process, user,
            free_port, injection_homedir="/tmp", schedule_epoch_time=None,
            schedule_cron_exp=None, tags={}):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[1]
        fault_type = list(self.faultops_dict['APP'].keys())[1]

        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)
        # if 'jvm_process' name is passed, get pid of process
        if isinstance(jvm_process, str):
            jvm_process = self.get_process_id(jvm_process, process_uname=user)

        payload = {
            "memoryLoad": memoryload,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.endpoint.ep_name,
            "randomEndpoint": False,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
            "jvmProperties": {
                "javaHomePath": java_home_path,
                "jvmprocess": jvm_process,
                "user": user,
                "port": free_port
            }
        }

        return self.invoke_mangle_api(payload, fault_area, fault_type)

    def generate_file_handler_leak_fault(
            self, timeout, java_home_path, jvm_process, user,
            free_port, injection_homedir="/tmp", schedule_epoch_time=None,
            schedule_cron_exp=None, tags={}):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict.keys())[1]
        fault_type = list(self.faultops_dict['APP'].keys())[2]

        schedule = FaultBase.set_schedule(schedule_epoch_time, schedule_cron_exp)
        # if 'jvm_process' name is passed, get pid of process
        if isinstance(jvm_process, str):
            jvm_process = self.get_process_id(jvm_process, process_uname=user)

        payload = {
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.endpoint.ep_name,
            "randomEndpoint": False,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
            "jvmProperties": {
                "javaHomePath": java_home_path,
                "jvmprocess": jvm_process,
                "user": user,
                "port": free_port
            }
        }

        return self.invoke_mangle_api(payload, fault_area, fault_type)

    def generate_thread_leak_fault(self, timeout, java_home_path, jvm_process, user,
                             free_port, oom_req, injection_homedir="/tmp",
                             schedule_epoch_time=None, schedule_cron_exp=None,
                             tags={}):
        """
        # TODO:
        """
        fault_area = list(self.faultops_dict)[1]
        fault_type = list(self.faultops_dict['APP'].keys())[3]

        schedule = FaultBase.set_schedule(schedule_epoch_time,
                                          schedule_cron_exp)

        # if 'jvm_process' name is passed, get pid of process
        if isinstance(jvm_process, str):
            jvm_process = self.get_process_id(jvm_process, process_uname=user)

        payload = {
            "enableOOM": oom_req,
            "timeoutInMilliseconds": timeout * 1000,
            "injectionHomeDir": injection_homedir,
            "endpointName": self.endpoint.ep_name,
            "randomEndpoint": False,
            "schedule": None if not bool(schedule) else schedule,
            "tags": None if not bool(tags) else tags,
            "jvmProperties": {"javaHomePath": java_home_path,
                              "jvmprocess": jvm_process, "user": user,
                              "port": free_port}
        }

        return self.invoke_mangle_api(payload, fault_area, fault_type)


class FaultOperations(object):
    """
    This class contains operations related to fault APIs
    """

    def __init__(self, mangle_api_obj):
        self.mangle_api_obj = mangle_api_obj

    @utilities.retry(retries=5, exceptions=RuntimeError, sleep=10)
    def remediate_fault(self, task_id):
        """
        Remediates fault using provided task ID
        """
        faults = Faults(self.mangle_api_obj)
        output = faults.remediate(task_id)

        log.info("%s *** Fault remediation output ***\n\n%s\n",
                 plugin_name, output)

        if ("REMEDIATION" in output[1]["taskType"]) and \
                (output[1]["initialized"] is True):
            log.info("%s *** Fault remediation started ***", plugin_name)
        else:
            log.error("%s *** FAILED to remediate fault ***", plugin_name)