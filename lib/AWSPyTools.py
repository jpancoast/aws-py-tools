#!/usr/bin/env python

import getopt
import os
import time
import re
import pprint

import pdb

import boto.ec2

import cPickle as pickle

try:
    import netaddr
except ImportError, e:
    print "Missing netaddr module.  Install with: sudo pip install netaddr"
    print "If you don't have pip, do this first: sudo easy_install pip"
    exit(2)


class AWSPyTools():

    def __init__(self, region='region', environment='env', loadFromFile=True, debug=False):
        self.instancesDict = {}
        self.securityGroupsDict = {}
        self.interfacesDict = {}
        self.allInfo = {}

        self.fileBasePath = '/tmp'
        self.loadFromFile = loadFromFile

        self.awsRegion = region
        self.awsEnv = environment

        self.fileAge = 60 * 60  # 60s * 60m

        self.dictFile = environment + "-" + region + ".dict"
        if debug:
            print "dictFile: " + self.dictFile

        self.debug = debug

        self.__connect()
        self.__loadOrDownload()

    def getVolumes(self):
        #vols = conn.get_all_volumes(filters={ 'tag:' + config['tag_name']: config['tag_value'] })
        vols = self.conn.get_all_volumes()
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

                sgs = self.conn.get_all_security_groups()

                for sg in sgs:
                    """
                    Figure key on both, make it easier to analyze?
                    """
                    self.securityGroupsDict[sg.id] = pickle.dumps(sg)
                    self.securityGroupsDict[sg.name] = pickle.dumps(sg)

                self.__save()

    def revokeSGRule(self, type, sg, rule, grant):
        if type == 'egress':
            self.conn.revoke_security_group_egress(group_id=sg.id, ip_protocol=rule.ip_protocol, from_port=rule.from_port, to_port=rule.to_port, src_group_id=grant.group_id, cidr_ip=grant.cidr_ip)
        elif type == 'ingress':
            self.conn.revoke_security_group(group_id=sg.id, ip_protocol=rule.ip_protocol, from_port=rule.from_port, to_port=rule.to_port, src_security_group_group_id=grant.group_id, cidr_ip=grant.cidr_ip)
        

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
        print "getAllInstanceInfo"

        instances = self.conn.get_only_instances()

        for instance in instances:
            print instance.groups
            self.instancesDict[instance.id] = instance

        self.__save()
        return self.instancesDict

    def interfaces(self):
        print "interfaces"
        interfaces = self.conn.get_all_network_interfaces()

        for interface in interfaces:
            print interface

        self.__save()
        return self.interfacesDict

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

        if len(self.instancesDict.keys()) > 0:
            allTheThings['instances'] = self.instancesDict

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

    def __connect(self):
        self.conn = boto.ec2.connect_to_region(
            self.awsRegion, profile_name=self.awsEnv)


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
