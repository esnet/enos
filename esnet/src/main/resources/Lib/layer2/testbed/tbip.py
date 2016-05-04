#/usr/bin/python
#
# ESnet Network Operating System (ENos) Copyright (c) 2015, The Regents
# of the University of California, through Lawrence Berkeley National
# Laboratory (subject to receipt of any required approvals from the
# U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this
# software, please contact Berkeley Lab's Innovation & Partnerships
# Office at IPO@lbl.gov.
#
# NOTICE.  This Software was developed under funding from the
# U.S. Department of Energy and the U.S. Government consequently retains
# certain rights. As such, the U.S. Government has been granted for
# itself and others acting on its behalf a paid-up, nonexclusive,
# irrevocable, worldwide license in the Software to reproduce,
# distribute copies to the public, prepare derivative works, and perform
# publicly and display publicly, and to permit other to do so.
#

""" This module manages IP allocation/deallocation."""

import sys
import math
from net.es.netshell.api import Resource, Container

PROPERTIES = 'properties'

DNSNAME = 'dnsname'
NETMASK = 'netmask'
HOSTTYPE = 'host-type'
RESOURCEOWNER = 'owner'
RESOURCETYPE = 'type'
OPERATING_SYSTEM = 'operating_system'
PROJECTID = 'projectID'
DESCRIPTION = 'description'
IPV4ADDRESS = 'ipv4address'
IPV4_FIRST = 'ipv4_first_octet'
IPV4_SECOND = 'ipv4_second_octet'
IPV4_THIRD = 'ipv4_third_octet'
IPV4_FOURTH = 'ipv4_fourth_octet'
IPV4_INT = 'ipv4_int'

IPRESOURCETYPE = 'ip'

RETRY_ATTEMPTS = 3



class IPManagement(object):
    """ IPManagement class provides the API to allocate and deallocate IPs"""

    IPCONTAINER = 'IPAddress'
    IPBASE = 256
    DBQ_LESSER = '$lt'
    DBQ_GREATER = '$gte'

    @staticmethod
    def get_ipcontainer():
        """ This method returns the IP container used to store IP address in persistent storage"""
        container = Container.getContainer(IPManagement.IPCONTAINER) 
        if container is None:
            Container.createContainer(IPManagement.IPCONTAINER)
            container = Container.getContainer(IPManagement.IPCONTAINER)
        return container

    @staticmethod
    def register_ip(ipresource):
        """ This method registers the given IP resource only if it is not already registered.
        It throws an error for duplicate registration. """

        container = IPManagement.get_ipcontainer()
        if ipresource is None:
            raise TypeError('ipresource is null')

        ipname = ipresource.getResourceName()
        ipexists = container.loadResource(ipname)
        if ipexists != None:
            raise ValueError('Attempting to register a registered IP')
        else:
            container.saveResource(ipresource)
            return ipresource

    @staticmethod
    def delete_ip(ipaddress):
        """ This method deletes the IP resource
        from persistent storage"""

        container = IPManagement.get_ipcontainer()

        if ipaddress is None:
            raise TypeError('ipaddress is null')

        ipresource = container.deleteResource(ipaddress)
        return ipresource

    @staticmethod
    def ip_to_number(ipaddress):
        """ This method converts the ip address into an integer
        """
        if ipaddress is None:
            raise TypeError('ipaddress is null')

        ipsplit = IPManagement.split_ip(ipaddress)
        ipnum = 0
        i = 3
        for ipadd in ipsplit:
            ipnum += ipadd * math.pow(IPManagement.IPBASE, i)
            i = i-1
        return ipnum

    @staticmethod
    def split_ip(ipaddress):
        """ This method splits ip and returns them as integer list
        """
        if ipaddress is None:
            raise TypeError('ipaddress is null')

        ip_split_str = ipaddress.split(".")
        ip_split_int = []

        for ipadd in ip_split_str:
            ippartial = int(ipadd)
            if ippartial >= 256 or ippartial < 0:
                raise ValueError("Invalid IP octet: "+ipadd)
            ip_split_int.append(ippartial)
        return ip_split_int

    @staticmethod
    def join_ip(ipoctets):
        """ This method creates ip from the list of octets
        """
        if ipoctets is None:
            raise TypeError('ipaddress is null')

        ipoctet_str = []
        for ipoctet in ipoctets:
            if ipoctet >= 256 or ipoctet < 0:
                raise ValueError("Invalid IP octet:"+ipoctet)
            ipoctet_str.append(str(ipoctet))

        ipaddress = '.'.join(ipoctet_str)
        return ipaddress

    @staticmethod
    def number_to_ip(input):
        """This method converts the given number back to integer"""
        ipoctet = []
        for i in range(0, 4):
            octet = input%256
            ipoctet.append(octet)
            input = input/256
        ipoctet.reverse()

        ipaddress = IPManagement.join_ip(ipoctet)
        return ipaddress

    @staticmethod
    def get_available_ip(lowip, highip):
        """ This method gets available ip address in the specified address"""
        container = IPManagement.get_ipcontainer()
        if lowip is None:
            raise TypeError('lower limit ip is null')

        if highip is None:
            raise TypeError('upper limit ip is null')

        lowipnumber = IPManagement.ip_to_number(lowip)
        highipnumber = IPManagement.ip_to_number(highip)

        rangequery = {}
        rangequery[IPManagement.DBQ_LESSER] = highipnumber
        rangequery[IPManagement.DBQ_GREATER] = lowipnumber

        query = {}
        key = PROPERTIES+"."+IPV4_INT
        query[key] = rangequery

        ipresources = container.loadResources(query)

        ipresourcemap = {}
        for ipres in ipresources:
            ipresourcemap[ipres.properties[IPV4_INT]] = 1

        iprange = highipnumber-lowipnumber
        if len(ipresources) >= iprange:
            raise ValueError("All IPs in this range have been allocated.")
        
        ipaddress = ""
        for i in range(int(lowipnumber), int(highipnumber)):
            if float(i) not in ipresourcemap:
                ipaddress = IPManagement.number_to_ip(i)
                break
        return ipaddress

def register_ip(dnsname, owner, pid, resourcetype, osname, description, ipaddress, netmask):
    """ This method creates the IP resource from the given arguments
    and registers it in persistent storage """
    if ipaddress is None or ipaddress == "":
        print 'ERROR: ipaddress is required'
        return

    try:
        int(netmask)
    except ValueError:
        print 'Netmask must be an integer'
        return

    ipresource = Resource(ipaddress)
    ipresource.properties[DNSNAME] = dnsname
    ipresource.properties[RESOURCETYPE] = IPRESOURCETYPE
    ipresource.properties[RESOURCEOWNER] = owner
    ipresource.properties[HOSTTYPE] = resourcetype
    ipresource.properties[OPERATING_SYSTEM] = osname
    ipresource.properties[PROJECTID] = pid
    ipresource.properties[DESCRIPTION] = description
    ipresource.properties[NETMASK] = netmask
    ipresource.properties[IPV4ADDRESS] = ipaddress

    ipoctets = IPManagement.split_ip(ipaddress)
    ipresource.properties[IPV4_FIRST] = ipoctets[0]
    ipresource.properties[IPV4_SECOND] = ipoctets[1]
    ipresource.properties[IPV4_THIRD] = ipoctets[2]
    ipresource.properties[IPV4_FOURTH] = ipoctets[3]

    ipint = IPManagement.ip_to_number(ipaddress)
    ipresource.properties[IPV4_INT] = ipint

    try:
        IPManagement.register_ip(ipresource)
    except ValueError:
        print 'ERROR: Attempting duplicate registration. IP already exists'
        return
    except TypeError:
        print 'ERROR: Registration failed. Please check input arguments'
        return

    print '%s/%s registered' % (ipresource, netmask)


def delete_ip(ipaddress):
    """ This method attempts to delete the given IP
    from Persistent storage"""
    if ipaddress is None:
        print 'ERROR: ipaddress is null'
        return

    try:
        IPManagement.delete_ip(ipaddress)
        print 'Deleted IP resource: %s' %(ipaddress)
    except TypeError:
        print 'ERROR: ipresource is null'
        return
    except Exception:
        print 'ERROR: Exception caught while deleting IP resource: %s' %(ipaddress) 


def allocate_ip(dnsname, owner, pid, resourcetype, osname, description, lowip, highip, netmask):
    """ This method creates the IP resource from the given arguments
    and registers it in persistent storage """
    success = 0
    attempt = 0
    while success == 0 and attempt < RETRY_ATTEMPTS:
        try:
            ipaddress = IPManagement.get_available_ip(lowip, highip)
            if ipaddress is None:
                print "ERROR: Cannot allocate IP"
            else:
                register_ip(dnsname, owner, pid, resourcetype, \
                    osname, description, ipaddress, netmask)
                success = 1
        except ValueError:
            print 'ERROR: No addresses found in the specified range'
        except TypeError:
            print 'ERROR: Invalid input. Please check input arguments'
        attempt = attempt + 1

    if success == 0:
        print "ERROR: Failed to allocate IP resource"


def get_ip(lowip, highip):
    """ This method gets the next available IP in the given range """

    ipaddress = IPManagement.get_available_ip(lowip, highip)
    print "Next available IP"
    print ipaddress


def print_help():
    "Help message for ip management utility"
    print "ESnet Testbed IP Utility"
    print "tbip <cmd> <cmds options>"
    print " Commands are:"
    print "\thelp"
    print "\t\tPrints this help."
    print "\tregister <dnsname>  <owner> <projectid> <type> <os> <description> \
<ip> <netmask>"
    print "\t\tRegisters IP resource"
    print "\tdelete <ip> "
    print "\t\tDeletes IP resource"
    print "\tgetip <lowip> <highip> "
    print "\t\tGet next available IP in the range"
    print "\tallocate <dnsname>  <owner> <projectid> <type> <os> <description> \
<lowip> <highip> <netmask>"
    print "\t\tAllocates next available IP resource and registers IP resource information"


if __name__ == '__main__':
    argv = sys.argv

    if len(argv) == 1:
        print_help()
        sys.exit()
    cmd = argv[1]
    if cmd == "help":
        print_help()
    elif cmd == "register":
        if (len(argv)) != 10:
            print "ERROR: Argument mismatch"
            print_help()
            sys.exit()
        else:
            resource_dns = argv[2]
            resource_owner = argv[3]
            resource_pid = argv[4]
            resource_type = argv[5]
            resource_os = argv[6]
            resource_description = argv[7]
            resource_ip = argv[8]
            resource_netmask = argv[9]
            register_ip(resource_dns, resource_owner, resource_pid, resource_type, \
                resource_os, resource_description, resource_ip, resource_netmask)
    elif cmd == "delete":
        if (len(argv)) != 3:
            print "ERROR: Argument mismatch"
            print_help()
            sys.exit()
        else:
            resource_ip = argv[2]
            delete_ip(resource_ip)
    elif cmd == "getip":
        if(len(argv)) != 4:
            print "ERROR: Argument mismatch"
            print_help()
            sys.exit()
        else:
            lowip = argv[2]
            highip = argv[3]
            get_ip(lowip, highip)
    elif cmd == "allocate":
        if (len(argv)) != 11:
            print "ERROR: Argument mismatch"
            print_help()
            sys.exit()
        else:
            resource_dns = argv[2]
            resource_owner = argv[3]
            resource_pid = argv[4]
            resource_type = argv[5]
            resource_os = argv[6]
            resource_description = argv[7]
            resource_lowip = argv[8]
            resource_highip = argv[9]
            resource_netmask = argv[10]
            allocate_ip(resource_dns, resource_owner, \
                resource_pid, resource_type, \
                resource_os, resource_description, \
                resource_lowip, resource_highip, resource_netmask)
