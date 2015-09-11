#!/usr/bin/env python


"""
Create a snapshot for a given volume id.

Usage:
    create_snapshot.py (--vol_id=<vol_id>) (--profile=<profile>)

Options:
    --help  Show this screen
    --version  Show version
    -v, --vol_id=<vol_id> Volume ID to make a snapshot of
    -p, --profile=<profile_name> Boto profile to use to connect. If not given, will attempt to use ENV variables.
"""

VERSION = '0.1'

import os
import sys
import pprint


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


    if arguments['--vol_id'] is not None:
        vol_id = arguments['--vol_id']

    if arguments['--profile'] is not None:
        profile = arguments['--profile']


    print "---------------"
    print "Boto Profile: " + str(profile)
    print "Volume ID: " + str(vol_id)
    print "---------------\n"


if __name__ == "__main__":
    main(sys.argv)