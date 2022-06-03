import paramiko
import logging

from vmware.mjolnir.constants import Constants as constants

log = logging.getLogger(__name__)
plugin_name = constants.PLUGIN_NAME

class SshServer(object):
    def __init__(self, hostname, username=None, password=None, ssh_port=None):
        self.hostname = hostname
        # Create a new SSH client object
        self.client = paramiko.SSHClient()
        # Set SSH key parameters to auto accept unknown hosts
        # self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if username:
            self.username = username
        if password:
            self.password = password
        self.ssh_port = ssh_port

    def connect(self):
        self.client.connect(hostname=self.hostname, username=self.username,
                            password=self.password, port=self.ssh_port)

    def ssh(self, command=None, timeout=60):
        if not command:
            raise Exception('Must provide a command for ssh!')
        log.debug('%s *** Executing Command: %s ***',
                  plugin_name, command)
        stdin, stdout, stderr = self.client.exec_command(command=command,
                                                         timeout=timeout)
        out = stdout.read().decode("utf-8")
        err = stderr.read().decode("utf-8")
        return out, err, stdout.channel.recv_exit_status()

    def ssh_background(self, command=None):
        """
        execute a non-blocking command. Do not return anything
        """
        if not command:
            raise Exception('Must provide a command for execCommand!')
        log.debug('%s *** Executing Command: %s ***',
                  plugin_name, command)
        self.client.exec_command(command=command)

    def close(self):
        self.client.close()
