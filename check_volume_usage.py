#!/usr/bin/env python

"""
Create a snapshot for a given volume id.

Usage:
    check_aws_limits.py (--profile=<profile>) (--region=<region>)

Options:
    --help  Show this screen
    --version  Show version
    -p, --profile=<profile_name> Boto profile to use to connect. If not given, will attempt to use ENV variables.
    -r, --region=<region> Region
"""

VERSION = '0.1'

import os
import sys
import pprint
import datetime

import boto.ec2


try:
    from docopt import docopt
except ImportError, e:
    print "Missing docopt module.  Install with: sudo pip install docopt"
    print "If you don't have pip, do this first: sudo easy_install pip"
    exit(2)


"""
Author: James Pancoast
Email: jpancoast@gmail
"""


def main(argv):
    arguments = docopt(
        __doc__, version=str(os.path.basename(__file__)) + " " + VERSION, options_first=False)

    pp = pprint.PrettyPrinter(indent=4)

    profile = None
    region = None

    if arguments['--profile'] is not None:
        profile = arguments['--profile']

    if arguments['--region'] is not None:
        region = arguments['--region']

    print "---------------"
    print "Boto Profile: " + str(profile)
    print "Region: " + str(region)
    print "---------------\n"

    volume_info = {}
    volume_info['standard'] = []
    volume_info['io1'] = []
    volume_info['gp2'] = []

    ec2_conn = boto.ec2.connect_to_region(region, profile_name=profile)

    volumes = ec2_conn.get_all_volumes()

    '''
    Types:
    io1: provisioned iops, ssd
    standard: magnetic
    gp2: general purpose ssd
    '''
    for volume in volumes:
        volume_info[volume.type].append(volume)
        '''
        print "volume.id: " + str(volume.id)
        print "volume.create_time: " + str(volume.create_time)
        print "volume.status: " + str(volume.status)
        print "volume.size: " + str(volume.size)
        print "volume.snapshot_id: " + str(volume.snapshot_id)
        #print str(volume.attach_data) #An attachmentset object
        print "volume.zone: " + str(volume.zone)
        print "volume.type: " + str(volume.type)
        print "volume.iops: " + str(volume.iops)
        print "volume.encrypted: " + str(volume.encrypted)


        print "-------"
        '''


    for type in volume_info:

        if len(volume_info[type]) > 0:
            print "Type: " + type
    
            for volume in volume_info[type]:
                print "volume.id: " + str(volume.id)
                print "volume.create_time: " + str(volume.create_time)
                print "volume.status: " + str(volume.status)
                print "volume.size: " + str(volume.size)
                print "volume.snapshot_id: " + str(volume.snapshot_id)
                #print str(volume.attach_data) #An attachmentset object
                print "volume.zone: " + str(volume.zone)
                print "volume.type: " + str(volume.type)
                print "volume.iops: " + str(volume.iops)
                print "volume.encrypted: " + str(volume.encrypted)

                print "----"

            print "----------------"


if __name__ == "__main__":
    main(sys.argv)