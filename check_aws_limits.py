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

    ec2_conn = boto.ec2.connect_to_region(region, profile_name=profile)

    account_attributes = ec2_conn.describe_account_attributes()

    Turns out this doesn't give me what I need...

    
    for blah in account_attributes:
        pp.pprint(blah)
        print "----------"


if __name__ == "__main__":
    main(sys.argv)