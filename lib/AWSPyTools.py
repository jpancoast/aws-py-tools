#!/usr/bin/env python

import getopt
import os
import time
import re
import pprint

import pdb

import boto.ec2
import boto.rds2
import boto.ec2.elb
import boto.elasticache

import cPickle as pickle

try:
    import netaddr
except ImportError, e:
    print "Missing netaddr module.  Install with: sudo pip install netaddr"
    print "If you don't have pip, do this first: sudo easy_install pip"
    exit(2)

'''
TODO:
    'objectify' elasticache, rds, instance, interfaces, lbs
'''


class AWSPyTools():

    def __init__(self, region='region', environment='env', loadFromFile=True, debug=False):
        self.instancesDict = {}
        self.securityGroupsDict = {}
        self.interfacesDict = {}
        self.lbDict = {}
        self.allInfo = {}
        self.rds_instances_dict = {}
        self.elasticache_clusters_dict = {}

        self.fileBasePath = '/tmp'
        self.loadFromFile = loadFromFile

        self.awsRegion = region
        self.awsEnv = environment

        self.fileAge = 60 * 60  # 60s * 60m

        self.dictFile = environment + "-" + region + ".dict"
        if debug:
            print "dictFile: " + self.dictFile

        self.debug = debug

        self.conn = None
        self.lb_conn = None
        self.rds_conn = None
        self.elasticache_conn = None

        self.__loadOrDownload()

    def get_ec2_conn(self):
        if self.conn is None:
            self.__ec2_connect()

        return self.conn

    def get_lb_conn(self):
        if self.lb_conn is None:
            self.__lb_connect()

        return self.lb_conn

    def get_rds_conn(self):
        if self.rds_conn is None:
            self.__rds_connect()

        return self.rds_conn

    def get_elasticache_conn(self):
        if self.elasticache_conn is None:
            self.__elasticache_connect()

        return self.elasticache_conn

    def __elasticache_connect(self):
        self.elasticache_conn = boto.elasticache.connect_to_region(
            self.awsRegion, profile_name=self.awsEnv)

    def __ec2_connect(self):
        self.conn = boto.ec2.connect_to_region(
            self.awsRegion, profile_name=self.awsEnv)

    def __lb_connect(self):
        self.lb_conn = boto.ec2.elb.connect_to_region(
            self.awsRegion, profile_name=self.awsEnv)

    def __rds_connect(self):
        self.rds_conn = boto.rds2.connect_to_region(
            self.awsRegion, profile_name=self.awsEnv)

    def getVolumes(self):
        #vols = conn.get_all_volumes(filters={ 'tag:' + config['tag_name']: config['tag_value'] })
        vols = self.get_ec2_conn().get_all_volumes()
        return vols

    def loadSecurityGroups(self):
        if len(self.securityGroupsDict.keys()) == 0:
            if self.debug:
                print "securityGroups"

            tempDict = {}

            if self.loadFromFile:
                if self.debug:
                    print "Loading from File"

                with open(self.fileBasePath + '/' + self.dictFile, 'r') as f:
                    tempDict = pickle.load(f)
                    self.securityGroupsDict = tempDict['securityGroups']
            else:
                if self.debug:
                    print "Loading From Amazon"

                sgs = self.get_ec2_conn().get_all_security_groups()

                for sg in sgs:
                    """
                    Figure key on both, make it easier to analyze?
                    """
                    self.securityGroupsDict[sg.id] = pickle.dumps(sg)
                    self.securityGroupsDict[sg.name] = pickle.dumps(sg)

                self.__save()

    def revokeSGRule(self, type, sg, rule, grant):
        if type == 'egress':
            self.get_ec2_conn().revoke_security_group_egress(group_id=sg.id, ip_protocol=rule.ip_protocol,
                                                             from_port=rule.from_port, to_port=rule.to_port, src_group_id=grant.group_id, cidr_ip=grant.cidr_ip)
        elif type == 'ingress':
            self.get_ec2_conn().revoke_security_group(group_id=sg.id, ip_protocol=rule.ip_protocol, from_port=rule.from_port,
                                                      to_port=rule.to_port, src_security_group_group_id=grant.group_id, cidr_ip=grant.cidr_ip)

    def getAllSecurityGroups(self, vpc_id=None, idOn='sgName'):
        self.loadSecurityGroups()
        allGroups = {}

        for sgIdOrName in self.securityGroupsDict:
            sg = pickle.loads(self.securityGroupsDict[sgIdOrName])

            if vpc_id is None or sg.vpc_id == vpc_id:
                if idOn == 'sgName':
                    if not sgIdOrName.startswith('sg-'):
                        allGroups[sg.name] = sg
                elif idOn == 'sgId':
                    if sgIdOrName.startswith('sg-'):
                        allGroups[sg.id] = sg

        return allGroups

    def getSecurityGroup(self, nameOrId):
        self.loadSecurityGroups()

        if nameOrId not in self.securityGroupsDict:
            return None
        else:
            return pickle.loads(self.securityGroupsDict[nameOrId])

    def getSecurityGroupNameFromId(self, sgId):
        self.loadSecurityGroups()

        temp = pickle.loads(self.securityGroupsDict[sgId])

        return temp.name

    def instances(self):
        instances = self.get_ec2_conn().get_only_instances()

        for instance in instances:
            self.instancesDict[instance.id] = instance

        self.__save()
        return self.instancesDict

    def get_all_elasticache_clusters(self):
        elasticache_clusters = self.get_elasticache_conn(
        ).describe_cache_clusters()

        for elasticache_cluster in elasticache_clusters['DescribeCacheClustersResponse']['DescribeCacheClustersResult']['CacheClusters']:
            self.elasticache_clusters_dict[
                elasticache_cluster['CacheClusterId']] = elasticache_cluster

        self.__save()
        return self.elasticache_clusters_dict

    def get_all_rds_instances(self):
        rds_instances = self.get_rds_conn().describe_db_instances()

        for rds_instance in rds_instances['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances']:

            self.rds_instances_dict[
                rds_instance['Endpoint']['Address']] = rds_instance

        self.__save()
        return self.rds_instances_dict

    def interfaces(self):
        interfaces = self.get_ec2_conn().get_all_network_interfaces()

        for interface in interfaces:
            self.interfacesDict[interface.id] = interface

        self.__save()
        return self.interfacesDict

    def loadBalancers(self):
        lbs = self.get_lb_conn().get_all_load_balancers()

        for lb in lbs:
            self.lbDict[lb.name] = lb

        self.__save()
        return self.lbDict

    def listSecurityGroups(self, vpc_id=None, idOn='sgName'):
        self.loadSecurityGroups()

        names = []

        for sgIdOrName in self.securityGroupsDict:
            sg = pickle.loads(self.securityGroupsDict[sgIdOrName])

            if vpc_id is None or sg.vpc_id == vpc_id:
                if idOn == 'sgName':
                    if not sgIdOrName.startswith('sg-'):
                        names.append(sgIdOrName)
                elif idOn == 'sgId':
                    if sgIdOrName.startswith('sg-'):
                        names.append(sgIdOrName)

        return names

    '''
        "Private" methods
    '''

    def __save(self):
        allTheThings = {}

        if len(self.securityGroupsDict.keys()) > 0:
            allTheThings['securityGroups'] = self.securityGroupsDict

        if len(self.interfacesDict.keys()) > 0:
            allTheThings['interfaces'] = self.interfacesDict

        if len(self.lbDict.keys()) > 0:
            allTheThings['loadBalancers'] = self.interfacesDict

        if len(self.instancesDict.keys()) > 0:
            allTheThings['instances'] = self.instancesDict

        if len(self.rds_instances_dict.keys()) > 0:
            allTheThings['rds_instances'] = self.rds_instances_dict

        with open(self.fileBasePath + '/' + self.dictFile, 'wb') as f:
            pickle.dump(allTheThings, f, pickle.HIGHEST_PROTOCOL)

    def __loadOrDownload(self):
        if self.debug:
            print "load or download"

        if self.loadFromFile:
            '''
            Attempting to load from file, we may not, though!
            '''
            if not os.path.isfile(self.fileBasePath + '/' + self.dictFile):
                self.loadFromFile = False
            else:
                fileNewerThan = time.time() - self.fileAge
                fileAge = os.path.getmtime(
                    self.fileBasePath + '/' + self.dictFile)

                print "FileNewerThan: " + str(fileNewerThan)
                print "fileAge: " + str(fileAge)

                if fileAge < fileNewerThan:
                    print "less than"
                    self.loadFromFile = False
                else:
                    print "greater than"


class SecurityGroup():

    def __init__(self, sgDict, nameOrId):
        self.sgObject = pickle.loads(sgDict[nameOrId])
        self.__convert(sgDict, nameOrId)

    def __str__(self):
        desc = "Security Group: \n\tName: " + self.name + "\n"
        desc += "\tID: " + self.id + "\n"
        desc += "\tvpc_id: " + self.vpc_id + "\n"

        desc += "\n\tIngress Rules:\n"

        index = 0

        for rule in self.rules['ingress']:
            if index > 0:
                desc += "\n"

            if rule['type'] == 'CIDR':
                desc += "\t\tCIDR: " + str(rule['cidr']) + "\n"
                desc += "\t\tProto: " + str(rule['proto']) + "\n"
                desc += "\t\tfrom_port: " + str(rule['from_port']) + "\n"
                desc += "\t\tto_port: " + str(rule['to_port']) + "\n"

            else:
                desc += "\t\tSG Name: " + str(rule['sgName']) + "\n"
                desc += "\t\tSG ID: " + str(rule['sgId']) + "\n"
                desc += "\t\tProto: " + str(rule['proto']) + "\n"
                desc += "\t\tfrom_port: " + str(rule['from_port']) + "\n"
                desc += "\t\tto_port: " + str(rule['to_port']) + "\n"

            index += 1

        desc += "\n\tEgress Rules:\n"

        index = 0

        for rule in self.rules['egress']:
            if index > 0:
                desc += "\n"

            if rule['type'] == 'CIDR':
                desc += "\t\tCIDR: " + str(rule['cidr']) + "\n"
                desc += "\t\tProto: " + str(rule['proto']) + "\n"
                desc += "\t\tfrom_port: " + str(rule['from_port']) + "\n"
                desc += "\t\tto_port: " + str(rule['to_port']) + "\n"

            else:
                desc += "\t\tSG Name: " + str(rule['sgName']) + "\n"
                desc += "\t\tSG ID: " + str(rule['sgId']) + "\n"
                desc += "\t\tProto: " + str(rule['proto']) + "\n"
                desc += "\t\tfrom_port: " + str(rule['from_port']) + "\n"
                desc += "\t\tto_port: " + str(rule['to_port']) + "\n"

            index += 1

        return desc

    def __convert(self, sgDict, nameOrId):
        self.vpc_id = self.sgObject.vpc_id
        self.id = self.sgObject.id
        self.name = self.sgObject.name

        self.rules = {}

        self.rules['ingress'] = []
        self.rules['egress'] = []

        for rule in self.sgObject.rules:
            for grant in rule.grants:
                self.rules['ingress'].append(
                    self.__formatRules(sgDict, rule, grant))

        for rule in self.sgObject.rules_egress:
            for grant in rule.grants:
                self.rules['egress'].append(
                    self.__formatRules(sgDict, rule, grant))

    def __formatRules(self, sgDict, rule, grant):
        tempRule = {}

        if str(grant).startswith('sg-'):
            '''We have a Amazon SG id'''
            resg = re.compile('^(sg-.*)-\d{12}$')
            for sgId in resg.match(str(grant)).groups():
                tempSgObject = pickle.loads(sgDict[sgId])

                tempRule['sgId'] = sgId

            tempRule['sgName'] = str(tempSgObject.name)

            tempRule['type'] = 'groupName'  # group rule, NOT CIDR
            tempRule['cidr'] = None

            tempRule['proto'] = str(rule.ip_protocol)
            tempRule['from_port'] = str(rule.from_port)
            tempRule['to_port'] = str(rule.to_port)

        else:
            '''CIDR BABY!'''
            tempRule['sgId'] = None
            tempRule['sgName'] = None

            tempRule['type'] = 'CIDR'
            tempRule['cidr'] = netaddr.IPNetwork(str(grant))

            tempRule['proto'] = str(rule.ip_protocol)
            tempRule['from_port'] = str(rule.from_port)
            tempRule['to_port'] = str(rule.to_port)

        return tempRule


'''
Can probably deprecate the following ParseOptions class now that I've figured out docopt
'''


class ParseOptions():

    def __init__(self, argv):
        self.argv = argv
        return None

    def getAwsOptions(self):
        options, remainder = getopt.getopt(self.argv[1:], 'e:r:v:',
                                           [
            'environment=',
            'region=',
            'vpc_id='
        ]
        )

        environment = None
        region = None
        vpc_id = None

        for opt, arg in options:
            if opt in ('-e', '--environment'):
                environment = arg

            if opt in ('-r', '--region'):
                region = arg

            if opt in ('-v', '--vpc_id'):
                vpc_id = arg

        if environment is None or region is None:
            self.usage()
            exit(2)

        self.environment = environment
        self.region = region

        return(environment, region, vpc_id)

    def usage(self):
        print "\nUsage: " + self.argv[0] + " -e|--environment=<environment.  Environment is the 'profile' name from ~/.aws/config> -r|--region=<region> -v|--vpc_id=<vpc ID>"
        print "\t-e|--environment REQUIRED"
        print "\t-r|--region OPTIONAL (us-west-2 default)"
        print "\t-v|--vpc_id OPTIONAL"
        print ""
