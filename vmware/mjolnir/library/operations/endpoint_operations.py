"""
Copyright 2017 VMware, Inc. All rights reserved. -- VMware confidential
"""
import logging
from vmware.mjolnir.library.api.endpoints import *
from vmware.mjolnir.library.operations.common_operations import CommonOps
from vmware.mjolnir.infrastructure import utilities
from vmware.mjolnir.constants import Constants as constants

log = logging.getLogger(__name__)
plugin_name = constants.PLUGIN_NAME


class EndpointOperations(object):
    """
    This class contains operations related to Endpoints
    """

    def __init__(self, mangle_api_obj, remote_machine_obj):
        self.mangle_api_obj = mangle_api_obj
        self.ep_ip = remote_machine_obj.ip
        self.ep_ssh_port = remote_machine_obj.ssh_port
        self.ep_user = remote_machine_obj.username
        self.ep_password = remote_machine_obj.password
        self.ep_name = CommonOps().get_ep_name(self.ep_ip)
        self.ep_cred_name = CommonOps().get_ep_cred_name(self.ep_ip)
        self.remote_machine_obj = remote_machine_obj

    def setup_fault_infra(self):
        """
        Create a setup like create endpoint endpoint if doesn't exist
        """
        self.add_endpoint_credential()
        self.test_remote_machine_endpoint_connection()
        self.add_endpoint()

    def add_endpoint_credential(self):
        """
        Add endpoint credential if it doesn't exist. Update
        """
        endpoint_credential_obj = EndpointCredential(self.mangle_api_obj)

        if self.is_endpoint_credential_exist(endpoint_credential_obj):
            # Updating endpoint credential
            log.debug("%s *** Endpoint credential %s already exists. Updating"
                      " it ***", plugin_name, self.ep_name)
            status, output = endpoint_credential_obj.update(
                self.ep_cred_name, self.ep_user, self.ep_password)
            log.debug("%s *** Output of update endpoint credential ***"
                      "\n\n%s\n", plugin_name, output)
        else:
            # Creating new endpoint credential
            log.debug("%s *** Creating Endpoint Credential ***", plugin_name)
            status, output = endpoint_credential_obj.add(
                self.ep_cred_name, self.ep_user, self.ep_password)
            log.debug("%s *** Output of add endpoint credential ***"
                      "\n\n%s\n", plugin_name, output)

        if status:
            log.debug("%s *** Waiting for endpoint credential action to"
                      " finish ***", plugin_name)
            self.is_endpoint_credential_exist(endpoint_credential_obj)

        return endpoint_credential_obj

    def test_remote_machine_endpoint_connection(self):
        """
        Testing connection for endpoint credential
        """
        payload = self.get_remote_endpoint_payload()

        log.debug("%s *** Testing Endpoint Connection ***", plugin_name)
        test_connection_obj = TestConnection(self.mangle_api_obj)

        status, output = test_connection_obj.test(payload)
        log.debug("%s *** output of test endpoint connection API ***\n\n%s\n",
                  plugin_name, output)

    def add_endpoint(self):
        """
        Creating endpoint if does not exist
        """
        log.debug("%s *** Creating Endpoint ***", plugin_name)
        endpoints_obj = Endpoints(self.mangle_api_obj)
        if self.is_endpoint_exist(endpoints_obj):
            log.debug("%s *** Endpoint %s already exists. Skipping creating"
                      " it ***", plugin_name, self.ep_name)
        else:
            payload = self.get_remote_endpoint_payload()
            status, output = endpoints_obj.add(payload)
            log.debug("%s *** output of add endpoint API ***\n\n%s\n",
                      plugin_name, output)
        return endpoints_obj

    @utilities.retry(retries=5, exceptions=RuntimeError, sleep=10)
    def is_endpoint_credential_exist(self, endpoint_credential_obj):
        """
        Checks if endpoint credential exists
        """
        found = False
        status, output = endpoint_credential_obj.get()
        # TODO: need to handle invalid credential error
        if output['content'] != []:
            for ep_cred_output in output['content']:
                if self.ep_ip in ep_cred_output["name"]:
                    found = True
        return found

    @utilities.retry(retries=5, exceptions=RuntimeError, sleep=10)
    def delete_endpoint_credential(self, endpoint_credential_obj):
        """
        Checks if endpoint credential exists
        """
        status, output = endpoint_credential_obj.delete(
            self.ep_cred_name)

        if not status:
            log.error("%s *** DELETE endpoint credential API FAILED with"
                      " output ***\n\n%s\n", plugin_name, output)

        if not self.is_endpoint_credential_exist(endpoint_credential_obj,
                                                 self.ep_cred_name):
            log.debug("%s *** Endpoint credential %s deletion SUCCESSFUL"
                      " ***", plugin_name, self.ep_cred_name)

    @utilities.retry(retries=5, exceptions=RuntimeError, sleep=10)
    def is_endpoint_exist(self, endpoints_obj):
        """
        Checks if endpoint exists
        """
        status, output = endpoints_obj.get()

        found = False
        if status:
            for idx, output_dict in enumerate(output['content']):
                if self.ep_name in output_dict["name"]:
                    found = True
        return found

    @utilities.retry(retries=5, exceptions=RuntimeError, sleep=10)
    def delete_endpoint(self, endpoints_obj):
        """
        Deletes the given endpoint
        """
        status, output = endpoints_obj.delete(self.ep_name)

        if not status:
            log.error("%s *** DELETE endpoint API FAILED with output ***"
                      "\n\n%s\n", plugin_name, output)

        if not self.is_endpoint_exist(endpoints_obj, self.ep_name):
            log.debug("%s *** Endpoint %s deletion SUCCESSFUL ***",
                      plugin_name, self.ep_name)

    def get_remote_endpoint_payload(self):
        """
        Creating payload for endpoint and testconnetion
        """
        payload = '{"name": "%s", "endPointType": "MACHINE",' \
                  '"credentialsName": "%s",' \
                  '"remoteMachineConnectionProperties": {"host": "%s",' \
                  '"osType": "LINUX","sshPort": %s,"timeout": 1000}}' % (
                      self.ep_name, self.ep_cred_name, self.ep_ip, self.ep_ssh_port)
        log.debug("%s *** payload for endpoint & test-connection ***\n\n%s\n",
                  plugin_name, payload)
        return payload


class EndpointGroupOperations(object):
    """
    This class contains operations related to Endpoints
    """

    def __init__(self, mangle_api_obj, endpoints,
                 name=None, group_type="MACHINE"):
        self.mangle_api_obj = mangle_api_obj
        self.ep_name = name if name else CommonOps().get_ep_random_group_name()
        self.group_type = group_type
        self.endpoints = endpoints

    def create_endpoint_group(self):
        """
        Creating an endpoint group from given endpoints
        """
        endpointgroup_obj = EndpointGroup(self.mangle_api_obj)
        payload = self._get_endpoint_group_payload()
        status, output = endpointgroup_obj.add(payload)
        log.debug("%s *** output of add endpoint API ***\n\n%s\n",
                  plugin_name, output)

    def add_endpoint_group(self):
        """
        Add endpoint group if does not exist
        """
        log.debug("%s *** Creating Endpoint Group ***", plugin_name)
        endpointgroup_obj = EndpointGroup(self.mangle_api_obj)
        if self.is_endpoint_group_exist(endpointgroup_obj):
            log.debug("%s *** Endpoint Group%s already exists. Skipping creating"
                      " it ***", plugin_name, self.ep_name)
        else:
            self.create_endpoint_group()

    @utilities.retry(retries=5, exceptions=RuntimeError, sleep=10)
    def is_endpoint_group_exist(self, endpointgroup_obj):
        """
        Checks if endpoint group exists
        """
        found = False
        status, output = endpointgroup_obj.get()
        if output['content']:
            for ep_group in output['content']:
                if self.ep_name in ep_group["name"]:
                    found = True
        return found

    @utilities.retry(retries=5, exceptions=RuntimeError, sleep=10)
    def delete_endpoint_group(self):
        """
        Checks if endpoint credential exists
        """
        endpointgroup_obj = EndpointGroup(self.mangle_api_obj)
        status, output = endpointgroup_obj.delete(self.ep_name)
        if not status:
            log.error("%s *** DELETE endpoint group API FAILED with"
                      " output ***\n\n%s\n", plugin_name, output)
        if not self.is_endpoint_group_exist(endpointgroup_obj):
            log.debug("%s *** Endpoint group %s deletion SUCCESSFUL"
                      " ***", plugin_name, self.ep_name)

    def _get_endpoint_group_payload(self):
        """
        Creating payload for endpoint groups
        """
        endpoints = [endpoint.ep_name for endpoint in self.endpoints]
        payload = {"endPointType": "ENDPOINT_GROUP",
                   "name": self.ep_name,
                   "endpointGroupType": self.group_type,
                   "endpointNames": endpoints}
        log.debug("%s *** payload for endpoint groups***\n\n%s\n",
                  plugin_name, payload)
        return payload
