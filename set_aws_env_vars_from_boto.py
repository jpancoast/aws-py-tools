#!/usr/bin/env python

"""
Create a snapshot for a given volume id.

Usage:
    create_snapshot.py (--profile=<profile>)

Options:
    --help  Show this screen
    --version  Show version
    -p, --profile=<profile_name> Boto profile to use.
"""

VERSION = '0.1'


import sys
import os

from boto.compat import ConfigParser

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

"""
TODO:
    Read from aws/.config as well, or instead of.
"""

def main(argv):
    arguments = docopt(
        __doc__, version=str(os.path.basename(__file__)) + " " + VERSION, options_first=False)

    config_file = os.path.expanduser('~/.boto')

    
    if arguments['--profile'] is not None:
        profile = arguments['--profile']

    print "---------------"
    print config_file
    print "Boto Profile: " + str(profile)
    print "---------------\n"

    '''
    AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY
    AWS_DEFAULT_REGION
    '''
    profile_found = False

    with open(config_file) as fp:
        config = ConfigParser()
        config.readfp(fp)
        profiles = config.sections()

    profile_search_string = "profile " + profile

    for config_profile in profiles:
        if config_profile == profile_search_string:
            profile_found = True

            aws_region = None

            if config.has_option(config_profile, 'region'):
                aws_region = config.get(config_profile, 'region')

            aws_access_key_id = config.get(config_profile, 'aws_access_key_id' )
            aws_secret_access_key = config.get(config_profile, 'aws_secret_access_key' )


            print "Copy and paste the following into your shell:"
            print "export AWS_ACCESS_KEY_ID=" + aws_access_key_id
            print "export AWS_SECRET_ACCESS_KEY=" + aws_secret_access_key

            if aws_region is not None:
                print "export AWS_DEFAULT_REGION=" + aws_region



    if not profile_found:
        print "Error: couldn't find the profile you requested: " + profile

if __name__ == "__main__":
    main(sys.argv)