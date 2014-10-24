#!/usr/bin/env python


import sys
import getopt
import signal
import pdb
import time
import os


from boto.ec2.autoscale import LaunchConfiguration
from boto.ec2.autoscale import AutoScaleConnection

import boto


'''
NOTE:
    Amazon will not let you delete a launch configuration that is attached to an asg
'''

def main(argv):
    signal.signal(signal.SIGINT, signal_handler)

    (env, region, dry_run, use_env_vars) = parse_options()

    if use_env_vars:
        if 'AWS_ACCESS_KEY_ID' in os.environ and 'AWS_SECRET_ACCESS_KEY' in os.environ and 'AWS_DEFAULT_REGION' in os.environ:
            aws_access_key = os.environ['AWS_ACCESS_KEY_ID']
            aws_secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
            region = os.environ['AWS_DEFAULT_REGION']
        else:
            print "either your access key (AWS_ACCESS_KEY_ID), secret key (AWS_SECRET_ACCESS_KEY), or region (AWS_DEFAULT_REGION) isn't in an environment variable."
            exit(2)

        conn = boto.ec2.autoscale.connect_to_region(
            region, aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
    else:
        print "Using command line options..."

        '''
        Have to do this because boto library defaults to environment variables first if they exist to connect to Amazon.
            If I'm using command line things for boto, I don't want it to do that...
        '''
        if 'AWS_ACCESS_KEY_ID' in os.environ:
            del os.environ['AWS_ACCESS_KEY_ID']
        
        if 'AWS_SECRET_ACCESS_KEY' in os.environ:
            del os.environ['AWS_SECRET_ACCESS_KEY']
    
        if 'AWS_DEFAULT_REGION' in os.environ:
            del os.environ['AWS_DEFAULT_REGION']

        conn = boto.ec2.autoscale.connect_to_region(region, profile_name=env)

    all_launch_configs = get_all_launch_configs(conn)
    all_asgs = get_all_auto_scaling_groups(conn)
    used_lcs = determine_used_lcs(all_asgs)
    unused_lcs = determine_unused_lcs(all_launch_configs, used_lcs)

    if len(unused_lcs) > 0:
        delete_unused_lcs(conn, unused_lcs, dry_run)
    else:
        print "No unused Launch Configurations..."
        if dry_run:
            print "\t(Dry run anyway...)"


def delete_unused_lcs(conn, unused_lcs, dry_run):
    sleep_delay = 2

    for lc_name in unused_lcs:
        lc = unused_lcs[lc_name]

        if dry_run:
            print "Dry Run, not actually deleting: " + lc.name
        else:
            print "Deleting launch config: " + lc.name
            response = lc.delete()
            print "\t Deleted launch config: " + lc.name + " Response: [" + str(response) + "]"
            time.sleep(sleep_delay)


def determine_unused_lcs(all_lcs, used_lcs):
    unused_lcs = {}

    for key in all_lcs:
        if key not in used_lcs:
            unused_lcs[key] = all_lcs[key]

    return unused_lcs


def determine_used_lcs(all_asgs):
    used_lcs = {}

    for asg_name in all_asgs:
        asg_lc_name = all_asgs[asg_name].launch_config_name
        used_lcs[asg_lc_name] = asg_lc_name

    return used_lcs


def get_all_launch_configs(conn):
    all_launch_configs = {}

    nextToken = "start"

    while nextToken is not None:
        if nextToken == 'start':
            lcs = conn.get_all_launch_configurations(max_records=100)
        else:
            lcs = conn.get_all_launch_configurations(
                max_records=100, next_token=nextToken)

        for lc in lcs:
            all_launch_configs[lc.name] = lc

        if len(all_launch_configs) % 100 == 0:
            nextToken = lcs.next_token
        else:
            nextToken = None

    return all_launch_configs


def get_all_auto_scaling_groups(conn):
    all_asgs = {}

    nextToken = "start"

    while nextToken is not None:
        if nextToken == 'start':
            asgs = conn.get_all_groups(max_records=100)
        else:
            asgs = conn.get_all_groups(max_records=100, next_token=nextToken)

        for asg in asgs:
            all_asgs[asg.name] = asg

        if len(all_asgs) % 100 == 0:
            nextToken = asgs.next_token
        else:
            nextToken = None

    return all_asgs


def parse_options():
    options, remainder = getopt.getopt(sys.argv[1:], 'e:r:dh',
    [
        'environment=',
        'region=',
        'dry_run',
        'help'
    ]
    )

    print_help = False
    use_env_vars = False
    environment = None
    region = None
    dry_run = False

    for opt, arg in options:
        if opt in ('-e', '--environment'):
            environment = arg

        if opt in ('-r', '--region'):
            region = arg

        if opt in ('-d', '--dry_run'):
            dry_run = True

        if opt in ('-h', '--help'):
            print_help = True

    if print_help:
        usage()
        exit(2)

    if environment is None and region is None:
        use_env_vars = True
        print "Attempting to use environment variables. If you want to use your boto profiles instead, do a '" + sys.argv[0] + " --help' to find out how!"

    return(environment, region, dry_run, use_env_vars)


def usage():
    print "\nUsage: " + sys.argv[0] + " -e|--environment=<environment. Environment is an entry in your boto file> -r|--region=<region> -d|--dry_run -h|--help"
    print "\t-e|--environment REQUIRED (if using boto profile)"
    print "\t-r|--region REQUIRED (if using boto profile)"
    print "\t-d|--dry_run OPTIONAL"
    print "\t-h|--help OPTIONAL"
    print ""


def signal_handler(signal, frame):
    print sys.argv[0] + " exited via keyboard interrupt."
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
