"""
Copyright 2017 VMware, Inc. All rights reserved. -- VMware confidential
"""


# HTTP Methods Constant(s)
GET = "GET"
PUT = "PUT"
POST = "POST"
DELETE = "DELETE"


class Faults(object):

    def __init__(self, mangle_api):
        self.mangle_api = mangle_api

        # set endpoints for fault(s)
        self.fault_endpoint = "/faults"
        self.api_endpoint_dict = {
            "CPU": self.fault_endpoint + "/cpu",
            "MEMORY": self.fault_endpoint + "/memory",
            "PROCESSKILL": self.fault_endpoint + "/kill-process",
            "DISKIO": self.fault_endpoint + "/diskIO",
            "FILEHANDLERLEAK": self.fault_endpoint + "/filehandler-leak",
            "KERNELPANIC": self.fault_endpoint + "/kernel-panic",
            "DISKSPACE": self.fault_endpoint + "/disk-space",
            "NETWORK": self.fault_endpoint + "/network-fault",
            "THREADLEAK": self.fault_endpoint + "/thread-leak",
            "STOPSVC": self.fault_endpoint + "/stop-service",
            "CLOCKSKEW": self.fault_endpoint + "/clockSkew",
            "NWPARTITION": self.fault_endpoint + "/network-partition"
        }

    def inject(self, fault_type, payload):
        """
        Injects fault based on type and with provided payload
        """
        return self.mangle_api.send(
            POST, self.api_endpoint_dict[fault_type], data=payload)

    def remediate(self, task_id):
        """
        Remediates an injected fault using taskId
        """
        return self.mangle_api.send(
            DELETE, "%s/%s" % (self.fault_endpoint, task_id))

    def rerun(self, task_id):
        """
        Reruns an injected fault using its taskId
        """
        return self.mangle_api.send(
            POST, "%s/%s" % (self.fault_endpoint, task_id))
