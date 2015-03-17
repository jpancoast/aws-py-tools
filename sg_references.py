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

    
    ingress_refs = {}
    egress_refs = {}
    interface_refs = {}
    instance_refs = {}
    lb_refs = {} 

    elasticache_refs = {}   #JAMESP
    rds_refs = {}   #JAMESP

    awsPyTools = AWSPyTools(
        region=region, environment=profile, loadFromFile=False, debug=debug)


    sg_looking_for = awsPyTools.getSecurityGroup(sgnameorid)
    sg_id = sg_looking_for.id 

    print "sg ID: " + sg_id + ", name from lib: " + sg_looking_for.name + "\n"

    sgs = awsPyTools.getAllSecurityGroups(vpc_id=vpc_id)
    interfaces = awsPyTools.interfaces()
    instances = awsPyTools.instances()
    load_balancers = awsPyTools.loadBalancers()
    rds_instances = awsPyTools.get_all_rds_instances()

    
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




    for interface_id in interfaces:
        groups = interfaces[interface_id].groups #This is a list

        for group in groups:
            if group.id == sg_id:
                interface_refs[interface_id] = interface_id


    for instance_id in instances:
        groups = instances[instance_id].groups

        for group in groups:
            if group.id == sg_id:
                instance_refs[instance_id] = instance_id
            

    for lb_name in load_balancers:
        lb = load_balancers[lb_name]
        
        for group_id in lb.security_groups:
            if group_id == sg_id:
                lb_refs[lb_name] = lb_name


    '''
    Output the info
    '''
    if len(ingress_refs) > 0:
        print sg_looking_for.name + " is referenced in the inbound rules in the following groups: "
        for ing_sg_id in ingress_refs:
            print "\t" + ingress_refs[ing_sg_id]
        print

    if len(egress_refs) > 0:
        print sg_looking_for.name + " is referenced in the outbound rules in the following groups: "
        
        for eg_sg_id in egress_refs:
            print "\t" + egress_refs[eg_sg_id]
        
        print

    if len(interface_refs) > 0:
        print sg_looking_for.name + " is used on the following interfaces: "
        
        for int_id in interface_refs:
            print "\t" + int_id
        
        print
    
    if len(instance_refs) > 0:
        print sg_looking_for.name + " is used on the following instances: "
        
        for instance_id in instance_refs:
            print "\t" + instance_id

        print

    if len(lb_refs) > 0:
        print sg_looking_for.name + " is used on the following Load Balancers: "

        for lb_name in lb_refs:
            print "\t" + lb_name

        print


def signal_handler(signal, frame):
    print sys.argv[0] + " exited via keyboard interrupt."
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)