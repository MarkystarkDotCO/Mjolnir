"""
Copyright 2021 VMware, Inc. All rights reserved. -- VMware confidential
"""

import logging
import urllib3
from vmware.mjolnir.constants import Constants as constants
import requests

log = logging.getLogger(__name__)
plugin_name = constants.PLUGIN_NAME


class RestApi(object):
    """
    Wrapper to interact with the Mangle REST API's

    Parameters
    ----------
    hostname: string
        IP Address or FQDN to Mangle
    username: string
        Mangle username
    password: string
        Mangle password
    prefix: string
        API prefix (will be append to the hostname)
    ssl_verify: bool, optional
        Perform SSL host verification (default=False)
    """

    def __init__(self, hostname, username, password,
                 prefix="/mangle-services/rest/api/v1", ssl_verify=False):
        """Init Mangle API with hostname and login credentials."""
        self.hostname = hostname
        self.username = username
        self.password = password
        self.prefix = prefix
        self.verify = ssl_verify
        self.request_kwargs = {
            "auth": (self.username, self.password),
            "verify": self.verify
        }
        if not ssl_verify:
            urllib3.disable_warnings()

    def __repr__(self):
        return 'MANGLEAPI(%r, %r, %r, %r)' % (self.hostname, self.username,
                                              self.password, self.prefix)

    def send(self, verb, ep_name, prefix=None, headers=None, **kwargs):
        """
        verb: string
        HTTP verb; 'GET', 'POST', 'PUT', 'DELETE'

        ep_name : string
            endpoint name, like (cluster-config)
            (https://{mangle-ip/hostname}/mangle-services/rest/api/v1/cluster-config)

        prefix: String
            default prefix is: "/mangle-services/rest/api/v1"

        kwargs: dict

        Returns
        --------
        will return True with api's json content on success else false with
                                                    respective cause of failure
        """
        kwargs['headers'] = headers
        if headers is None:
            kwargs['headers'] = {'Content-type': 'application/json'}

        prefix = self.prefix if prefix is None else prefix
        url = "".join(["https://", self.hostname, prefix, ep_name])
        log.debug("%s *** Running URL %s %s ***", plugin_name, verb, url)
        kwargs.update(self.request_kwargs)
        response = None
        try:
            response = requests.request(method=verb, url=url, **kwargs)
            json_response = {}
            if not response.status_code == 204:
                json_response = response.json()
            log.debug("%s *** %s API response %s = \n %s",
                      plugin_name, verb, ep_name, json_response)

            status_code = response.status_code
            if status_code not in [200, 201]:
                raise Exception('Failed url : {}, status_code: {}, response: {}'.format(
                    url, status_code, json_response))

            return response.status_code, json_response
        except Exception as error:
            log.error("Failed plugin: %s, error: %s", plugin_name, error.message)
            raise
