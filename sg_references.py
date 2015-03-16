#!/usr/bin/env python

"""
Tell us where a given SG is referenced (ie, other SG's, instances, and/or network interfaces)

Usage:
    sgReferences.py (--sgname=<sgname>) (--profile=<profile>) (--vpcid=<vpcid>) (--region=<region>) [(--debug)]

Options:
    --help  Show this screen
    --version   Show version
    -s, --sgname=<sgname>  Security Group Name or ID
    -v, --vpcid=<vpcid>  VPC ID.
    -p, --profile=<botoprofile>  Name of your boto profile to use to connect to AWS.
    -r, --region=<region> AWS Region
    --debug  Turn on debug output

"""

"""
Author: James Pancoast
Email: jpancoast@gmail.com 
twitter.com/jpancoast
"""

VERSION = '0.1'

import sys
import signal

from lib.AWSPyTools import AWSPyTools

try:
    from docopt import docopt
except ImportError, e:
    print "Missing docopt module.  Install with: sudo pip install docopt"
    print "If you don't have pip, do this first: sudo easy_install pip"
    exit(2)


def main(argv):
    signal.signal(signal.SIGINT, signal_handler)
    arguments = docopt(
        __doc__, version="sgReferences.py " + VERSION, options_first=False)

    profile = arguments['--profile']
    debug = arguments['--debug']
    sgnameorid = arguments['--sgname']
    vpc_id = arguments['--vpcid']
    region = arguments['--region']

    awsPyTools = AWSPyTools(
        region=region, environment=profile, loadFromFile=False, debug=debug)


    sg_looking_for = awsPyTools.getSecurityGroup(sgnameorid)
    sg_id = sg_looking_for.id 

    print "sg ID: " + sg_id + ", name from lib: " + sg_looking_for.name

    sgs = awsPyTools.getAllSecurityGroups(vpc_id=vpc_id)
    
    ingress_refs = {}
    egress_refs = {}

    
    for sgName in sgs:
        sg = sgs[sgName]

        '''
        Inbound rules
        '''
        if len(sg.rules) > 0:
            for rule in sg.rules:
                for grant in rule.grants:
                    if grant.group_id is not None:
                        if grant.group_id == sg_id:
                            ingress_refs[sg.id] = str(sg.name)
    
        '''
        Egress rules
        '''
        if len(sg.rules_egress) > 0:
            for rule in sg.rules_egress:
                for grant in rule.grants:
                    if grant.group_id is not None:
                        if grant.group_id == sg_id:
                            egress_refs[sg.id] = str(sg.name)


    if len(ingress_refs) > 0:
        print "Ingress Refs: "
        for ing_sg_id in ingress_refs:
            print ingress_refs[ing_sg_id]

    if len(egress_refs) > 0:
        print "Egress Refs: "
        for eg_sg_id in egress_refs:
            print egress_refs[eg_sg_id]

def signal_handler(signal, frame):
    print sys.argv[0] + " exited via keyboard interrupt."
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)