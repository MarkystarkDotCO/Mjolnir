# Copyright (C) 2021 VMware, Inc. All rights reserved.
import json
import logging

from vmware.mjolnir.constants import Constants as constants
from vmware.mjolnir.fault_injection import FaultInjection
from vmware.mjolnir.fault_teardown import FaultTeardown
from vmware.mjolnir.remote_machine_object import RemoteMachineObject

log = logging.getLogger(__name__)
plugin_name = constants.PLUGIN_NAME


def configure_mangle_server(server, username, password, port):
    """
    Args:
        server: Mangle Server ip
        username: Mangle Server username
        password: Mangle Server password
        port: Mangle Server port

    Returns: None

    """
    constants.MANGLE_SERVER = "{}:{}".format(server, port)
    constants.MANGLE_USERNAME = username
    constants.MANGLE_PASSWORD = password


def inject_fault(topology, remote_machine_objs, fault_type, fault_sub_type,
                 fpn=False, configure_mangle=True, **kwargs):
    """
    :param topology:
    :param remote_machine_objs:
    :param fault_type:
    :param fault_sub_type:
    :param fpn:
    :param configure_mangle:
    :param kwargs:
    :return: Task ids
    """
    if configure_mangle:
        configure_mangle_server(
            topology.get_constant("MANGLE_SERVER"),
            topology.get_constant("MANGLE_USERNAME"),
            topology.get_constant("MANGLE_PASSWORD"),
            topology.get_constant("MANGLE_PORT"))

    if not isinstance(remote_machine_objs, list):
        raise TypeError('remote_machine_objs must be instance of list')
    endpoint_machine_objs = get_remote_objects(remote_machine_objs,
                                               username=constants.ROOT_USER,
                                               fpn=fpn)

    fault_obj = FaultInjection(
        endpoint_machine_objs, fault_type, fault_sub_type, fault_payload=kwargs)
    return fault_obj.task_id_list


def inject_generic_fault(remote_machines, fault_type, fault_sub_type, **kwargs):
    """

    Args:
        remote_machines: list of remote_machine dicts
                        example: [{
                        'name': <name>,
                        'ip': <ip>,
                        'username': <username> (if not provided, root is set as default),
                        'password': <password>,
                        'ssh_port': <ssh> (if not provided, 22 is set as default)}]
        fault_type: fault type
        fault_sub_type: fault sub type
        **kwargs: Fault payload

    Returns: Mangle taskid for corresponding remote_machines after injection

    """
    if not isinstance(remote_machines, list):
        raise TypeError('remote_machine_objs must be instance of list')
    endpoint_machine_objs = get_remote_objects(remote_machines)
    fault_obj = FaultInjection(
        endpoint_machine_objs, fault_type, fault_sub_type, fault_payload=kwargs)
    return fault_obj.task_id_list


def clear_faults(task_ids):
    """
    Clears faults based on the provided task Ids
    """
    fault_teardown = FaultTeardown()
    fault_teardown.remediate_all_faults(task_ids)


def get_remote_objects(remote_machine_objs, username=None, fpn=False):
    obj_lst = []

    if fpn:
        def _get_attr(machine, attr):
            fh = open('/tmp/port_mapping_data.json', 'r')
            data = json.load(fh)
            log.debug(
                "%s: *** content of:: /tmp/port_mapping_data.json\n %s ***",
                plugin_name, data)
            fh.close()
            # using 'data' and 'machine' return the attr value
            for component, value in data.items():
                if component in machine.name:
                    all_fpn_machines = value
                    for fpn_machine in all_fpn_machines:
                        log.debug("%s fpn machines: %s", plugin_name,
                                  fpn_machine)
                        if machine.name.replace("_", ".") in fpn_machine['name']:
                            return fpn_machine[attr]

        for remote_machine in remote_machine_objs:
            machine_dict = {
                'name': get_attribute(remote_machine, 'name'),
                'ip': _get_attr(remote_machine, 'nat_ip'),
                'username': username if username else get_attribute(remote_machine, 'username'),
                'password': get_attribute(remote_machine, 'password'),
                'ssh_port': _get_attr(remote_machine, 'ssh_port'),
            }
            obj_lst.append(RemoteMachineObject(**machine_dict))
    else:
        for remote_machine in remote_machine_objs:
            machine_dict = {
                'name': get_attribute(remote_machine, 'name'),
                'ip': get_attribute(remote_machine, 'ip'),
                'username': username if username else get_attribute(remote_machine, 'username'),
                'password': get_attribute(remote_machine, 'password'),
                'ssh_port': get_attribute(remote_machine, 'ssh_port', 22)
            }
            obj_lst.append(RemoteMachineObject(**machine_dict))

    return obj_lst


def get_attribute(obj, attribute, default=None):
    """

    Args:
        obj: dictionary or object
        attribute: attribute
        default: default value if attribute is not set

    Returns: attribute value

    """
    if isinstance(obj, dict):
        return obj.get(attribute, default)
    else:
        return getattr(obj, attribute, default)
