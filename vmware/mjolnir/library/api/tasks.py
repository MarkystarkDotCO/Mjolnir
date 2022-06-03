"""
Copyright 2017 VMware, Inc. All rights reserved. -- VMware confidential
"""

# HTTP Methods Constant(s)
GET = "GET"
PUT = "PUT"
POST = "POST"
DELETE = "DELETE"


class Tasks(object):

    def __init__(self, mangle_api):
        self.mangle_api = mangle_api

        # set endpoints for task(s)
        self.task_endpoint = "/tasks"

    def get_all(self):
        """
        Gives details of all the tasks executed by Mangle
        """
        return self.mangle_api.send(GET, self.task_endpoint)

    def get(self, task_id):
        """
        Gives task details from Mangle using its id
        """
        return self.mangle_api.send(
            GET, "%s/%s" % (self.task_endpoint, task_id))

    def delete(self, task_id):
        """
        Delete task's entry from the application
        """
        return self.mangle_api.send(
            DELETE, "%s?tasksIds=%s" % (self.task_endpoint, task_id))
