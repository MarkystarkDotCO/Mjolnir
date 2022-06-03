"""
Copyright 2021 VMware, Inc. All rights reserved. -- VMware confidential
"""

from vmware.mjolnir.infrastructure import utilities
from vmware.mjolnir.constants import Constants as constants
import logging
import time

log = logging.getLogger(__name__)
plugin_name = constants.PLUGIN_NAME


class CommonOps(object):
    """
    common operations
    """

    @staticmethod
    def poll_fault_status(session_obj, fault_id, expected_status=None, raise_on_status=None,
                          timeout=120):
        """
        # TODO:
        """
        if expected_status is None:
            expected_status = ["INJECTED", "COMPLETED"]
        if raise_on_status is None:
            raise_on_status = ["NOT STARTED", "FAILED"]

        log.debug("%s *** fault id :: %s ***", plugin_name, fault_id)

        def get_task_status():
            """
            # TODO:
            """
            # build prefix to get the status of task
            prefix = '/tasks/%s' % fault_id
            ret_val, fault_status = session_obj.send("GET", prefix)
            log.debug("%s *** fault_status ***:: %s", plugin_name, fault_status)
            time.sleep(10)
            status = fault_status['mangleTaskInfo']['taskStatus']
            log.info("%s *** fault_status ***:: %s ", plugin_name, status)
            if status in raise_on_status:
                while True:
                    time.sleep(10)
                    log.error(" *** start debugging with Mangle Team ***")
                # raise RuntimeError(
                #     "Injection Status : {} : {}".format(status, fault_status['taskDescription']),
                #     fault_status)
            return status in expected_status

        utilities.poll(get_task_status, "Expected status to become %s.."
                       % expected_status, sleep=10, timeout=timeout)

    def get_ep_name(self, ep_ip):
        """
        Returns endpoint's name
        """
        self.ep_name = utilities.get_random_string(prefix="ep-"+ep_ip)
        return self.ep_name

    def get_ep_cred_name(self, ep_ip):
        """
        Returns endpoint credential name
        """
        # TODO: Need to update ep-cred-name with random string
        # self.ep_cred_name = utilities.get_random_string(prefix="ep-cred-"+self.ep_ip)
        return "ep-cred-%s" % ep_ip

    def get_ep_random_group_name(self):
        """
        Returns endpoint group name
        """
        return utilities.get_random_string(prefix="ep-group-")

    @staticmethod
    def get_task_details(session_obj, task_id):
        """
        # Returns Task details from its ID
        """
        # build prefix to get the status of task
        prefix = '/tasks/%s' % task_id
        ret_val, fault_details = session_obj.send("GET", prefix)
        log.info("%s *** fault details ***:: %s", plugin_name,
                 fault_details)
        return fault_details

