#!/usr/bin/env python

import os
import sys
import signal
import yaml

from lib.AWSPyTools import ParseOptions
from lib.AWSPyTools import AWSPyTools



def main(argv):
    signal.signal(signal.SIGINT, signal_handler)

    po = ParseOptions(sys.argv)
    (env, region, vpc_id) = po.getAwsOptions()

    debug = True


    awsPyTools = AWSPyTools(
        region=region, environment=env, loadFromFile=False, debug=debug)

    #vols = conn.get_all_volumes(filters={ 'tag:' + config['tag_name']: config['tag_value'] })
    for vol in awsPyTools.getVolumes():
        print vol

def signal_handler(signal, frame):
    print sys.argv[0] + " exited via keyboard interrupt."
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
