"""
Copyright 2021 VMware, Inc. All rights reserved. -- VMware confidential
"""

# HTTP Methods Constant(s)
GET = "GET"
PUT = "PUT"
POST = "POST"
DELETE = "DELETE"


class Common(object):

    def __init__(self, mangle_api):
        self.mangle_api = mangle_api
        self.api_endpoint = "/endpoints"


class Endpoints(Common):
    """
    This class contains CRUD methods related to Endpoint
    """
    def get(self):
        """
        Gets endpoint details
        :return:
        """
        return self.mangle_api.send(GET, self.api_endpoint)

    def add(self, payload):
        """
        Creates endpoint
        :param payload: payload in dict
        :return:
        """
        return self.mangle_api.send(POST, self.api_endpoint, data=payload)

    def update(self, payload):
        """
        Update Endpoint
        :param payload: payload in dict
        :return:
        """
        return self.mangle_api.send(PUT, self.api_endpoint, data=payload)

    def delete(self, endpoint_name):
        """
        Deletes Endpoint
        :param endpoint_name: name of the endpoint to delete
        :return:
        """
        api_endpoint = "{0}?endpointNames={1}".\
            format(self.api_endpoint, endpoint_name)
        return self.mangle_api.send(DELETE, api_endpoint)


class EndpointCredential(Common):
    """
    This class contains methods related to endpoint credentials
    """
    def get(self):
        """
        Gives endpoint credential details
        """
        api_endpoint = "{0}/credentials".format(self.api_endpoint)
        return self.mangle_api.send(GET, api_endpoint)

    def add(self, ep_cred_name, mp_username, mp_password):
        """
        Creates endpoint credentials
        :return:
        """
        api_endpoint = "{0}/credentials/remotemachine?name={1}" \
                       "&password={2}&username={3}".\
            format(self.api_endpoint, ep_cred_name, mp_password, mp_username)
        return self.mangle_api.send(POST, api_endpoint)

    def update(self, ep_cred_name, mp_username, mp_password):
        """
        Updates endpoint credentials
        :return:
        """
        api_endpoint = "{0}/credentials/remotemachine?name={1}" \
                       "&password={2}&username={3}".\
            format(self.api_endpoint, ep_cred_name, mp_password, mp_username)
        return self.mangle_api.send(PUT, api_endpoint)

    def delete(self, endpoint_credential_name):
        """
        Deletes endpoint credentials
        :return:
        """
        api_endpoint = "{0}/credentials?credentialNames={1}".\
            format(self.api_endpoint, endpoint_credential_name)
        return self.mangle_api.send(DELETE, api_endpoint)


class TestConnection(Common):
    """
    This class contains methods related to test connection for endpoint
    """
    def test(self, payload):
        """
        Tests connection for endpoint
        :param payload: payload in dict
        :return:
        """
        api_endpoint = "{0}/testEndpoint".format(self.api_endpoint)
        return self.mangle_api.send(POST, api_endpoint, data=payload)


class EndpointGroup(Common):
    """
    This class contains CRUD methods related to Endpoint
    """
    def __init__(self, mangle_api):
        super().__init__(mangle_api)
        self.api_prefix = "/mangle-services/rest/api/v2"

    def get(self):
        """
        Gives ENDPOINT_GROUP details
        """
        api_endpoint = "{0}/type/ENDPOINT_GROUP".format(self.api_endpoint)
        return self.mangle_api.send(GET, api_endpoint)

    def add(self, payload):
        """
        Creates endpoint group
        :param payload: payload in dict
        :return:
        """
        return self.mangle_api.send(POST, self.api_endpoint,
                                    prefix=self.api_prefix, json=payload)

    def update(self, payload):
        """
        Updates endpoint group
        :param payload: payload in dict
        :return:
        """
        return self.mangle_api.send(PUT, self.api_endpoint,
                                    prefix=self.api_prefix, json=payload)

    def delete(self, endpoint_name):
        """
        Deletes endpoint group
        :return:
        """
        api_endpoint = "{0}?endpointNames={1}". \
            format(self.api_endpoint, endpoint_name)
        return self.mangle_api.send(DELETE, api_endpoint)
