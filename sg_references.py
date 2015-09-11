#!/usr/bin/env python

"""
Tell us where a given SG is referenced (ie, other SG's, instances, and/or network interfaces)

Usage:
    sgReferences.py (--sgname=<sgname>) (--profile=<profile>) (--vpcid=<vpcid>) (--region=<region>) [(--debug)]

Options:
    --help  Show this screen
    --version   Show version
    -s, --sgname=<sgname>  Security Group Name or ID, CaSe SEnsITiVe
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

"""
TODO:
    If an ENI is the primary (ie, eth0) interface for an instance that's already been output, don't display it.
    Check on whether it lets you delete a sg that's used in a launch config.
    Do ENI's last, because they may have been changed either by elasticache or lb changes previous.
"""

VERSION = '0.1'

import sys
import signal
import pprint

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

    referenced = False

    ingress_refs = {}
    egress_refs = {}
    interface_refs = {}
    instance_refs = {}
    lb_refs = {}
    rds_refs = {}

    elasticache_refs = {}  # JAMESP

    awsPyTools = AWSPyTools(
        region=region, environment=profile, loadFromFile=False, debug=debug)

    sg_looking_for = awsPyTools.getSecurityGroup(sgnameorid)
    sg_id = sg_looking_for.id

    print "sg ID: " + sg_id + ", name/sgid given on cli: " + sgnameorid + ", name from lib: " + sg_looking_for.name + "\n"

    sgs = awsPyTools.getAllSecurityGroups(vpc_id=vpc_id)
    interfaces = awsPyTools.interfaces()
    instances = awsPyTools.instances()
    load_balancers = awsPyTools.loadBalancers()
    rds_instances = awsPyTools.get_all_rds_instances()
    elasticache_clusters = awsPyTools.get_all_elasticache_clusters()

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
                            referenced = True

        '''
        Egress rules
        '''
        if len(sg.rules_egress) > 0:
            for rule in sg.rules_egress:
                for grant in rule.grants:
                    if grant.group_id is not None:
                        if grant.group_id == sg_id:
                            egress_refs[sg.id] = str(sg.name)
                            referenced = True

    for interface_id in interfaces:
        groups = interfaces[interface_id].groups  # This is a list

        for group in groups:
            if group.id == sg_id:
                interface_refs[interface_id] = interface_id
                referenced = True

    for instance_id in instances:
        groups = instances[instance_id].groups

        for group in groups:
            if group.id == sg_id:
                instance_refs[instance_id] = instance_id
                referenced = True

    for lb_name in load_balancers:
        lb = load_balancers[lb_name]

        for group_id in lb.security_groups:
            if group_id == sg_id:
                lb_refs[lb_name] = lb_name
                referenced = True

    for rds_instance_id in rds_instances:
        rds_instance = rds_instances[rds_instance_id]

        for vpc_groups in rds_instance['VpcSecurityGroups']:
            if vpc_groups['VpcSecurityGroupId'] == sg_id:
                rds_refs[rds_instance_id] = rds_instance[
                    'DBInstanceIdentifier']
                referenced = True

    for elasticache_cluster in elasticache_clusters:
        for group in elasticache_clusters[elasticache_cluster]['SecurityGroups']:
            if group['SecurityGroupId'] == sg_id:
                elasticache_refs[elasticache_clusters[elasticache_cluster][
                    'CacheClusterId']] = elasticache_clusters[elasticache_cluster]['CacheClusterId']
                referenced = True

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

    if len(instance_refs) > 0:
        print sg_looking_for.name + " is used on the following instances: "

        for instance_id in instance_refs:
            print "\t" + instance_id

        print

    if len(interface_refs) > 0:
        print sg_looking_for.name + " is used on the following interfaces: "

        for int_id in interface_refs:
            print "\t" + int_id

        print

    if len(lb_refs) > 0:
        print sg_looking_for.name + " is used on the following Load Balancers: "

        for lb_name in lb_refs:
            print "\t" + lb_name

        print

    if len(rds_refs) > 0:
        print sg_looking_for.name + " is used on the following RDS Instances: "

        for instance_id in rds_refs:
            print "\t" + rds_refs[instance_id] + ", " + instance_id

        print

    if len(elasticache_refs) > 0:
        print sg_looking_for.name + " is used in the following elasticache clusters: "

        for elasticache_cluster_id in elasticache_refs:
            print "\t" + elasticache_cluster_id

        print

    if not referenced:
        print sg_looking_for.name + " is not referenced anywhere that I can find"
        print


def signal_handler(signal, frame):
    print sys.argv[0] + " exited via keyboard interrupt."
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
