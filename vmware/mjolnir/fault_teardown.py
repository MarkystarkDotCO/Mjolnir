"""
Copyright 2021 VMware, Inc. All rights reserved. -- VMware confidential
"""
import logging
from vmware.mjolnir.constants import Constants as constants
from vmware.mjolnir.infrastructure import utilities
from vmware.mjolnir.library.api.restapi import RestApi
from vmware.mjolnir.library.operations.fault_operations import FaultOperations
from vmware.mjolnir.library.operations.task_operations import TaskOperations

log = logging.getLogger(__name__)
plugin_name = constants.PLUGIN_NAME


class FaultTeardown(object):

    @property
    def mangleapi(self):
        """
        will return, Mangle server object
        """
        return RestApi(constants.MANGLE_SERVER, constants.MANGLE_USERNAME,
                       constants.MANGLE_PASSWORD)

    def remediate_all_faults(self, task_ids):
        """
        It remediates all the faults based on task IDs
        """
        task_ops = TaskOperations(self.mangleapi)
        fault_ops = FaultOperations(self.mangleapi)
        for task_id in task_ids:
            fault_type, status = task_ops.get_task_status(task_id)
            log.info("%s *** task status = %s", plugin_name, status)
            if ("INJECTED" in status and fault_type == 'INFRA') or (
                    "COMPLETED" in status and fault_type == 'APP'):
                fault_ops.remediate_fault(task_id)
                self.wait_for_remediation_to_complete(task_id)

    def wait_for_remediation_to_complete(self, task_id):
        """
        Waits for remediation to complete
        """
        expected_status = "COMPLETED"

        def get_status():
            task_ops = TaskOperations(self.mangleapi)
            fault_type, status = task_ops.get_task_status(task_id)
            return status in expected_status

        utilities.poll(get_status, "Expected status to become %s.."
                       % expected_status, sleep=10, timeout=constants.INFINITE_TIME_OUT)
