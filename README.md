aws-py-tools
============

Some random python aws tools I'm working on.

Scripts... and how to use them
------------------------------
checkSGForOutboundAll.py: This script checks all security groups in a region (and a specific VPC if provided) for 'outbound all', and removes that rule from any SG that has it.

    Usage:
        ./checkSGForOutboundAll.py -e|--environment=<environment.  Environment is the 'profile' name from ~/.aws/config> -r|--region=<region> -v|-vpc_id=<vpc ID>
            -e|--environment REQUIRED
            -r|--region OPTIONAL (us-west-2 default)
            -v|--vpc_id OPTIONAL

deleteLaunchConfigurations.py: This script deletes all unused launch configurations ina region.

    Usage:
        ./deleteLaunchConfigurations.py -e|--environment=<environment. Environment is an entry in your boto file> -r|--region=<region> -d|--dry_run -h|--help
            -e|--environment REQUIRED (if using boto profile)
            -r|--region REQUIRED (if using boto profile)
            -d|--dry_run OPTIONAL
            -h|--help OPTIONAL

Notes
-----
    - checkForExtraSGs.py isn't working right now.
