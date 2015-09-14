#!/usr/bin/env python


"""
Create a snapshot for a given volume id.

Usage:
    create_snapshot.py (--vol_id=<vol_id>) (--profile=<profile>) (--region=<region>)

Options:
    --help  Show this screen
    --version  Show version
    -v, --vol_id=<vol_id> Volume ID to make a snapshot of
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
    vol_id = None
    region = None

    formatted_desc_date = datetime.datetime.now().strftime('%m/%d/%Y')
    now_date = datetime.datetime.now() + datetime.timedelta(-15)
    description = "Compnor Data Volume Backup " + formatted_desc_date

    if arguments['--vol_id'] is not None:
        vol_id = arguments['--vol_id']

    if arguments['--profile'] is not None:
        profile = arguments['--profile']

    if arguments['--region'] is not None:
        region = arguments['--region']

    print "---------------"
    print "Boto Profile: " + str(profile)
    print "Volume ID: " + str(vol_id)
    print "Region: " + str(region)
    print "---------------\n"

    ec2_conn = boto.ec2.connect_to_region(region, profile_name=profile)

    try:
        volumes = ec2_conn.get_all_volumes(volume_ids=[vol_id])
    except boto.exception.EC2ResponseError, e:
        print "There was an ec2 error: "
        print "=========================="
        print e
        print "=========================="
        exit()


    for volume in volumes:
        print "Creating snapshot: " + description
        volume.create_snapshot(description=description)
        
        for snapshot in volume.snapshots():
            start_time = datetime.datetime.strptime(snapshot.start_time[:-5], '%Y-%m-%dT%H:%M:%S')

            if start_time < now_date:
                print "Deleting this one: " + snapshot.description
                snapshot.delete()


if __name__ == "__main__":
    main(sys.argv)