#!/usr/bin/env python

import os
import sys
import signal
import yaml

from AWSPyTools import ParseOptions
from AWSPyTools import AWSPyTools

from jinja2 import Template

'''
NOTE: 
    This isn't working yet.
    
Perhaps have a confgi file somewhere or something that maps env+region+vpc to all_security_groups playbook (or whatever playbook)
'''


def main(argv):
    signal.signal(signal.SIGINT, signal_handler)

    po = ParseOptions(sys.argv)
    (env, region, vpc_id) = po.getAwsOptions()

    baseTaskDir = "../../aws/"
    playbook = "../../aws/all_security_groups.yml"

    playbookData = {}
    taskData = {}
    sgNames = {}

    debug = False

    truncated_vpc_id = vpc_id  # JAMESP NEED TO FIX

    awsPyTools = AWSPyTools(
        region=region, environment=env, loadFromFile=False, debug=debug)

    envDataString = "Running in environment: " + env + ", region: " + region

    if vpc_id is not None:
        envDataString += ", vpc_id: " + vpc_id

    print envDataString

    try:
        with open(playbook) as f:
            playbookData = yaml.load(f)
    except:
        print "Couldn't load " + playbook + ", bad Yaml?"

    for includeBlock in playbookData[0]['pre_tasks']:
        taskFile = includeBlock['include']
        stack = ''
        appname = ''

        if 'stack' in includeBlock:
            stack = includeBlock['stack']

        if 'appname' in includeBlock:
            appname = includeBlock['appname']

        taskData = {}

        try:
            with open(baseTaskDir + taskFile) as f:
                taskData = yaml.load(f)
        except:
            print "couldn't load " + taskFile + ", bad Yaml?"

        template = Template(taskData[0]['local_action']['name'])

        actualSGName = template.render(
            stack=stack, appname=appname, truncated_vpc_id=truncated_vpc_id)

        sgNames[actualSGName] = actualSGName

    for sgName in sgNames:
        print sgName


def signal_handler(signal, frame):
    print sys.argv[0] + " exited via keyboard interrupt."
    sys.exit(0)


def usage():
    print "need to add directory... -d|--directory <path to playbook directory>"

if __name__ == "__main__":
    main(sys.argv)
