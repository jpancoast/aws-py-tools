#!/usr/bin/env python

"""
Rename a security group

Usage:
    rename_security_group.py (--newgroup=<newgroupname>) (--oldgroup=<oldgroupname>) (--profile=<profile>) (--vpcid=<vpcid>) (--region=<region>) [(--debug) (--check)]

Options:
    --help  Show this screen
    --version   Show version
    -n, --newgroup=<newgroupname>  New Security Group Name
    -o, --oldgroup=<oldgroupname> Old Security Group Name
    -v, --vpcid=<vpcid>  VPC ID.
    -p, --profile=<botoprofile>  Name of your boto profile to use to connect to AWS.
    -r, --region=<region> AWS Region
    --debug  Turn on debug output
    -c, --check  Run in check mode

"""

"""
Author: James Pancoast
Email: jpancoast@gmail.com 
twitter.com/jpancoast
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


'''
1. check to see if the 'old' group exists. Exit if it doesn't
    old and new can't be the same.
2. Check to see if new group exists.
    a. If new group exists. copy all old rules into new group.
    b. If new group does not exist, create new group with rules from old group.
3.  Check SG's where old group is referenced and add the same rules with the new group name.
4.  Check instances where old group is referenced and change them over to the new group.
5.  interfaces
6.  load Balancers
7.  rds'
8.  elasticache 
9.  Delete the old one.

    While adding the new group to an interface, make sure it's not there already!

    Be careful about when to load/reload info from AWS. We probably don't want to reload everything, but maybe we do in the case of interfaces after the instance sg's are changed
    CHECK MODE!
        If check mode, it just prints out what to do.

    Probably re-write library to use 'SecurityGroup' class, which has a 'rule' class.
'''


def main(argv):
    signal.signal(signal.SIGINT, signal_handler)
    arguments = docopt(
        __doc__, version="rename_security_group.py " + VERSION, options_first=False)

    profile = arguments['--profile']
    debug = arguments['--debug']
    check_mode = arguments['--check']
    new_group_name = arguments['--newgroup']
    old_group_name = arguments['--oldgroup']
    vpc_id = arguments['--vpcid']
    region = arguments['--region']

    awsPyTools = AWSPyTools(
        region=region, environment=profile, loadFromFile=False, debug=debug)

    '''
    Make sure the given group names are not the same
    '''
    if old_group_name.lower() == new_group_name.lower():
        print "can't move a group to itself (ie, the old group name and new group name are the same)"
        sys.exit(0)

    old_sg = awsPyTools.getSecurityGroup(old_group_name)

    '''
    Make sure old group exists
    '''
    if old_sg is None:
        print old_group_name + " Does not exist. Exiting"
        sys.exit(0)

    '''
    ingress_refs = {}
    egress_refs = {}
    interface_refs = {}
    instance_refs = {}
    lb_refs = {}
    rds_refs = {}
    sg_refs = {}
    '''

    '''
    sg_looking_for = awsPyTools.getSecurityGroup(sgnameorid)
    sg_id = sg_looking_for.id

    print "sg ID: " + sg_id + ", name/sgid given on cli: " + sgnameorid + ", name from lib: " + sg_looking_for.name + "\n"
    print "Renaming "

    sgs = awsPyTools.getAllSecurityGroups(vpc_id=vpc_id)
    interfaces = awsPyTools.interfaces()
    instances = awsPyTools.instances()
    load_balancers = awsPyTools.loadBalancers()
    rds_instances = awsPyTools.get_all_rds_instances()
    elasticache_clusters = awsPyTools.get_all_elasticache_clusters()

    for sgName in sgs:
        sg = sgs[sgName]

        if len(sg.rules) > 0:
            for rule in sg.rules:
                for grant in rule.grants:
                    if grant.group_id is not None:
                        if grant.group_id == sg_id:
                            ingress_refs[sg.id] = str(sg.name)
                            referenced = True

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


def signal_handler(signal, frame):
    print sys.argv[0] + " exited via keyboard interrupt."
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
