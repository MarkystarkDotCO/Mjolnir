"""
Copyright 2017 VMware, Inc. All rights reserved. -- VMware confidential
"""

import atexit
import pyVmomi
import re
import ssl
import time
import logging
from vmware.mjolnir.constants import Constants as constants
from pyVim.connect import SmartConnect, Disconnect

log = logging.getLogger(__name__)
plugin_name = constants.PLUGIN_NAME


class VsphereOperations(object):
    """
    # TODO
    """
    VIM_TYPES = {'datacenter': [pyVmomi.vim.Datacenter],
                 'vmwaredistributedvirtualdwitch':
                     [pyVmomi.vim.dvs.VmwareDistributedVirtualSwitch],
                 'datastore': [pyVmomi.vim.Datastore],
                 'resourcepool': [pyVmomi.vim.ResourcePool],
                 'distributedvirtual portgroup':
                     [pyVmomi.vim.dvs.DistributedVirtualPortgroup],
                 'network': [pyVmomi.vim.Network],
                 'clustercomputeresource': [pyVmomi.vim.ComputeResource],
                 'hostsystem': [pyVmomi.vim.HostSystem],
                 'datastoreSystem': [pyVmomi.vim.host.DatastoreSystem],
                 'virtualMachine': [pyVmomi.vim.VirtualMachine]}

    def get_vm_object(self, vm_ip, server_ip, server_username, server_password):
        """
        # TODO
        """
        try:
            log.info("%s *** Getting VM Object %s ***", plugin_name,
                     vm_ip)
            service_instance = self.get_service_instance(
                server_ip, server_username, server_password)
            content = service_instance.content
            vm_object = self.get_component_object(
                content, self.VIM_TYPES['virtualMachine'], vm_ip)
            return vm_object
        except Exception as e:
            log.error("%s *** Failed to get a VM object for %s ***",
                      plugin_name, vm_ip)
            log.error(e)

            raise Exception("%s *** Unable to get object for VM %s on server"
                            " %s. Please check server details ***",
                            plugin_name, vm_ip, server_ip)

    def power_on_vm(self, vm_object):
        """
        # TODO
        """
        log.info("%s *** Power-On VM %s ***", plugin_name, vm_object.name)
        task = vm_object.PowerOn()
        self.wait_for_task(task)
        while task.info.state not in [pyVmomi.vim.TaskInfo.State.success,
                                      pyVmomi.vim.TaskInfo.State.error]:
            time.sleep(1)
        if task.info.state == pyVmomi.vim.TaskInfo.State.success:
            return True
        else:
            return False

    def power_off_vm(self, vm_object):
        """
        # TODO
        """
        log.info("%s *** Power-Off VM %s ***", plugin_name, vm_object.name)
        task = vm_object.PowerOff()
        self.wait_for_task(task)
        while task.info.state not in [pyVmomi.vim.TaskInfo.State.success,
                                      pyVmomi.vim.TaskInfo.State.error]:
            time.sleep(1)
        if task.info.state == pyVmomi.vim.TaskInfo.State.success:
            return True
        else:
            return False

    def wait_for_task(self, task, wait_time=180, poll_interval=0, strict=True):
        """
        # TODO
        """
        start_time = time.time()
        while (time.time() - start_time) < wait_time:
            time.sleep(poll_interval)
            if task.info.state == "success":
                log.debug("%s *** Task %s is successful ***", plugin_name,
                          task.info.descriptionId)
                return True
            elif task.info.state == "error":
                log.error("%s *** Task %s threw an error ***", plugin_name,
                          task.info.descriptionId)
                if strict:
                    raise task.info.error
                else:
                    return False
        raise Exception("%s Task %s timed out after %d seconds, current state:"
                        " %s", plugin_name, task.info.descriptionId,
                        wait_time, task.info.state)

    def get_service_instance(self, server_ip, server_username, server_password,
                             port=443):
        """
        Gets service instnace given VC details
        :param server_ip: vCenter server IP
        :param server_username: vCenter server username
        :param server_password: vCenter server password
        :param port: 443
        :return: service instance object
        """
        service_instance = None
        try:
            log.debug("%s *** Called get service instance ***")
            ssl._create_default_https_context = ssl._create_unverified_context
            service_instance = SmartConnect(
                host=server_ip, user=server_username, pwd=server_password,
                port=port)
            log.debug("%s *** Connected to server having %s IP ***",
                      plugin_name, server_ip)
            atexit.register(Disconnect, service_instance)
            return service_instance
        except:
            log.error("%s *** Failed to get Service Instance for server with"
                      " IP %s ***", plugin_name, server_ip)
            raise Exception("%s Unable to connect to Server with IP %s. Please"
                            " check server details ***", plugin_name,
                            server_ip)

    def get_component_object(self, content, vimtype, vm_ip):
        """
        Gives the component object as per given vimtype for the matching name
        :param content: content of server
        :param vimtype: type of component
        :param name: name of component
        :return: object
        """
        component_obj = None
        container = content.viewManager.CreateContainerView(
            content.rootFolder, vimtype, True)
        components_list = container.view
        container.Destroy()

        for component in components_list:
            print(dir(component))
            for net_info in component.guest.net:
                for entry in net_info.ipConfig.ipAddress:
                    match = re.match("\d+.\d+.\d+.\d+", entry.ipAddress)
                    if match:
                        ip_address = entry.ipAddress
                        if ip_address in vm_ip:
                            component_obj = component
                            log.debug("%s *** Got component object for %s ***",
                                      plugin_name, vm_ip)
                            break
        return component_obj
