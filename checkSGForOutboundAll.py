#!/usr/bin/env python

import sys
import signal
import boto.ec2
import operator
import getopt

from AWSPyTools import ParseOptions
from AWSPyTools import AWSPyTools


def main(argv):
    signal.signal(signal.SIGINT, signal_handler)

    po = ParseOptions(sys.argv)
    (env, region, vpc_id) = po.getAwsOptions()

    debug = False

    awsPyTools = AWSPyTools(
        region=region, environment=env, loadFromFile=False, debug=debug)

    envDataString = "Running in environment: " + env + ", region: " + region

    if vpc_id is not None:
        envDataString += ", vpc_id: " + vpc_id

    print envDataString

    sgs = awsPyTools.getAllSecurityGroups(vpc_id=vpc_id)

    for sgName in sgs:
        sg = sgs[sgName]

        if len(sg.rules_egress) > 0:
            for rule in sg.rules_egress:
                for grant in rule.grants:
                    if (rule.from_port is None or rule.from_port == 'None') and (rule.to_port is None or rule.to_port == 'None') and (rule.ip_protocol == '-1') and (str(grant.cidr_ip) == '0.0.0.0/0'):
                        print str(sg.name) + " (" + sg.id + ") has OUTBOUND ALL, so I'm removing that rule"
                        print ""

                        awsPyTools.revokeSGRule('egress', sg, rule, grant)


def signal_handler(signal, frame):
    print sys.argv[0] + " exited via keyboard interrupt."
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
