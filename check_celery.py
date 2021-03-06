#!/usr/bin/env python

"""
check_celery.py
~~~~~~~~~

This is a monitoring plugin for Nagios NRPE or SSH. If required, ensure a copy of this is
placed in the following directory on the host machine: /usr/local/nagios/plugins/
"""

import sys
import requests
import json
from NagAconda import Plugin

check_api = Plugin("Used to determine the status of a Celery worker.", "1.0")

check_api.add_option("p", "port", "Port of the Celery host machine serving the Flower API. (default: 5555)", default=5555)
check_api.add_option("h", "host", "Host of the Celery worker instance. (default: localhost)", default="localhost")
check_api.add_option("a", "action", "The status check to perform. (nodeup, health)", default="health")
check_api.add_option("n", "node", "Check if a specified node is up. Used with `nodeup` action. (default: celery.ubuntu)", default="celery.ubuntu")
check_api.add_option("l", "limit", "Number of tasks in the past to check. (default: 100)", default=100)
check_api.add_option("u", "auth_user", "Auth Username (default: None)", default=None)
check_api.add_option("x", "auth_pass", "Auth Password (default: None)", default=None)

check_api.enable_status("warning")
check_api.enable_status("critical")

check_api.start()

if check_api.options.action not in ("nodeup", "health"):
    check_api.unknown_error("unknown action specified %s." % check_api.options.action)

if check_api.options.auth_user:
    auth = requests.auth.HTTPBasicAuth(check_api.options.auth_user,
                                       check_api.options.auth_pass)
else:
    auth = None

response = requests.get("http://%s:%d/api/workers" % (check_api.options.host, int(check_api.options.port)),
                        auth=auth)

try:
    response.raise_for_status()
except Exception as e:
    print e
    print "Status Critical, Flower API not reachable"
    sys.exit(2)

try:
    content = json.loads(response.content)
except Exception as e:
    check_api.unknown_error("%s health check response was malformed: %s" % (check_api.options.action, e))

if len(content) == 0:
    print "Status Warning, no Celery workers at the moment"
    sys.exit(1)

if check_api.options.action == "nodeup":
    if check_api.options.node not in content:
        print "Status Critical, {} node not found".format(check_api.options.node)
        sys.exit(2)
else:
    print "Status OK, {} nodes up".format(len(content))

check_api.set_status_message("Celery health check successful")

check_api.finish()

