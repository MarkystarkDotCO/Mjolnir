"""
Copyright 2017 VMware, Inc. All rights reserved. -- VMware confidential
"""

import logging
from vmware.mjolnir.constants import Constants as constants
from vmware.mjolnir.library.api.tasks import Tasks

log = logging.getLogger(__name__)
plugin_name = constants.PLUGIN_NAME


class TaskOperations(object):
    """
    This class contains operations related to task API
    These task API gives the details of task triggered on Mangle
    """

    def __init__(self, mangle_api_obj):
        self.mangle_api_obj = mangle_api_obj

    def get_task_status(self, fault_id):
        """
        Returns task status for given fault ID
        """
        fault_type = 'INFRA'
        tasks = Tasks(self.mangle_api_obj)
        output = tasks.get(fault_id)
        log.info("%s *** GET task details output *** = \n\n%s\n", plugin_name, output)
        if 'jvmprocess' in output[1]['taskDescription']:
            fault_type = 'APP'

        return fault_type, output[1]["mangleTaskInfo"]["taskStatus"]
