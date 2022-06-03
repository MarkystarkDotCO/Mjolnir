# Copyright (C) 2021 VMware, Inc. All rights reserved.

class RemoteMachineObject(object):
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get("name")
        self.ip = kwargs.get("ip")
        self.username = kwargs.get("username")
        self.password = kwargs.get("password")
        self.ssh_port = kwargs.get("ssh_port")

