#!/usr/bin/env python

import os
import sys
import signal
import yaml

#from lib.AWSPyTools import ParseOptions
from lib.AWSPyTools import AWSPyTools


from docopt import docopt


""" docopt_example.py
    
    Usage:
        docopt_example.py -h
        docopt_example.py <required> [-f | -g | -o ]
        docopt_example.py <repeating>...
    Options:
        -h,--help       : show this help message
        required        : example of a required argument
        repeating       : example of repeating arguments
        -f,--flag       : example flag #1
        -g,--greatflag  : example of flag #2
        -o,--otherflag  : example of flag #3
"""

""" createSnapShot.py
    
    Usage:
        createSnapShot.py -h | -r | -e
    Options:
        -h,--help       : help message

"""

def main(argv):
    signal.signal(signal.SIGINT, signal_handler)

#    po = ParseOptions(sys.argv)
#    (env, region, vpc_id) = po.getAwsOptions()

    debug = True


    awsPyTools = AWSPyTools(
        region=region, environment=env, loadFromFile=False, debug=debug)

    #vols = conn.get_all_volumes(filters={ 'tag:' + config['tag_name']: config['tag_value'] })
    for vol in awsPyTools.getVolumes():
        print vol
        print

def signal_handler(signal, frame):
    print sys.argv[0] + " exited via keyboard interrupt."
    sys.exit(0)


if __name__ == "__main__":
    args = docopt(__doc__)
    main(args)
