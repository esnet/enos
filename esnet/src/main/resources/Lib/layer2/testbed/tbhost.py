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

""" This module manages testbed hosts - creation, deletion, starting, stopping"""

from net.es.netshell.api import Resource, Container

from proxmoxer import ProxmoxAPI

from layer2.testbed import idmanager, proxmoxutil

import string
import time

HOST_CONTAINER = 'host'

HOSTNAME = 'host'
HOSTID = 'id'
HYPERVISOR = 'hypervisor'
OWNER = 'owner'
PROJECT = 'project'
PROPERTIES = 'properties'

PROPERTIES_OS = 'os'
PROPERTIES_OSTEMPLATE = 'ostemplate'
PROPERTIES_USER = 'user'
PROPERTIES_PASSWORD = 'password'
PROPERTIES_AUTHREALM = 'authrealm'
PROPERTIES_HYPERVISOR = 'hypervisor'
PROPERTIES_PORT = 'port'

PROPERTIES_CPUS = 'cpus'
PROPERTIES_STORAGE='storage'
PROPERTIES_MEMORY='memory'
PROPERTIES_SWAP='swap'
PROPERTIES_DISK='disk'

CONTROLPLANE_PREFIX = '192.168.120.'
CONTROLPLANE_NETMASK = 24

CONTROL_PLANE_INTERFACE = 'eth0'

DATAPLANE_VLAN4012 = 4012
DATAPLANE_VLAN4020 = 4020
DATAPLANE_PREFIX = '10.'
DATAPLANE_NETMASK = 24

CPUS = 1
STORAGE='local'
MEMORY=1024
SWAP=1024
DISK=10


INTERFACES = "ifaces"
IPADDRESS = "ipaddress"
VLAN = "vlan"

DEFAULT_PASSWORD = 'enos@testbed'


def exists(hostname):
    container = Container.getContainer(HOST_CONTAINER)
    if container.loadResource(hostname):
        return True
    else:
        return False

def createHostTemplateWithId(host, hypervisor, owner, project, hostid, os):
    """ Creates template for host that already has id and stores in persistent storage """
    container = Container.getContainer(HOST_CONTAINER)

    if not exists(host):

        #Create host resource and save
        hostresource = Resource(host)
        hostresource.properties[HOSTNAME] = host
        hostresource.properties[HOSTID] = hostid
        hostresource.properties[HYPERVISOR] = hypervisor
        hostresource.properties[OWNER] = owner
        hostresource.properties[PROJECT] = project
        hostresource.properties[PROPERTIES_OS] = os
        
        #set default lxc properties
        hostresource.properties[PROPERTIES_CPUS] = CPUS
        hostresource.properties[PROPERTIES_STORAGE] = STORAGE
        hostresource.properties[PROPERTIES_MEMORY] = MEMORY
        hostresource.properties[PROPERTIES_SWAP] = SWAP
        hostresource.properties[PROPERTIES_DISK] = DISK

        #commenting out unitl lxc code is integrated
        ostemplate = proxmoxutil.getostemplate(os)
        if ostemplate is None:
        	raise ValueError("OS Template does not exist. Please configure os template using proxmoxutil")
        else:
        	hostresource.properties[PROPERTIES_OSTEMPLATE] = ostemplate.properties[PROPERTIES_OSTEMPLATE]

        hostresource.properties[INTERFACES] = []

        container.saveResource(hostresource)
        
        return hostresource


    else:
        raise ValueError("Attempting to create duplicate host")


def createHostTemplate(host, hypervisor, owner, project, os):
    """ Gets id for host and creates template for host and stores in persistent storage """
    if not exists(host):
        #get next available id for host
        try:
            hostid = idmanager.allocate(host,owner,project)
            createHostTemplateWithId(host, hypervisor, owner, project, hostid, os)
        except ValueError as e:
            print e
    else:
        raise ValueError("ERROR: Host template exists.")


def buildlxc(host):
    """ Creates lxc in proxmox using given hostresource configuration """
    
    if not exists(host):
    	raise ValueError("Host template is missing. Please create host template")
    
    container = Container.getContainer(HOST_CONTAINER)
    hostresource = container.loadResource(host)
    
    #get proxmox user and hypervisor 
    userresource = proxmoxutil.listuser()
    if userresource is None:
    	raise ValueError("No proxmox user found!! Please use proxmoxutil command to update user credentials")
    		
    user = userresource.properties[PROPERTIES_USER]
    password = userresource.properties[PROPERTIES_PASSWORD]
    authrealm = userresource.properties[PROPERTIES_AUTHREALM]
    puser = user+'@'+authrealm
    	  	
    primary = proxmoxutil.listprimary()
    		
    if primary is None:
    	raise ValueError("Primary proxmox hypervisor not found!! Please use proxmoxutil command to update primary hypervisor")
    	
    hypervisor = primary.properties[PROPERTIES_HYPERVISOR]
    print "Authenticating "+puser +" on "+ hypervisor
    proxmox = ProxmoxAPI(hypervisor, user=puser, password=password, verify_ssl=False)
    node = proxmox.nodes(hostresource.properties[HYPERVISOR])
        		
    vmid = int(hostresource.properties[HOSTID])
    ostemplate = str(hostresource.properties[PROPERTIES_OSTEMPLATE])
    cpus = int(hostresource.properties[PROPERTIES_CPUS])
    memory = int(hostresource.properties[PROPERTIES_MEMORY])
    swap = int(hostresource.properties[PROPERTIES_SWAP])
    storage = hostresource.properties[PROPERTIES_STORAGE]
    disk = int(hostresource.properties[PROPERTIES_DISK])
    
    
    
        	      
    print "Building LXC with the following parameters:"
    print "Vmid: %d" %vmid
    print "Template: %s" %ostemplate
    print "Cpus: %d" %cpus
    print "Memory: %d" %memory
    print "Swap: %d" %swap
    print "Storage: %s" %storage
    print "Disk: %d" %disk 
    
    disksize="%dG"%(disk)

    node.lxc.create(vmid=vmid, ostemplate=ostemplate, password=DEFAULT_PASSWORD, memory=memory, swap=swap)
    print "Creating LXC....."
    time.sleep(30)
    print "Resizing rootfs"
    node.lxc(vmid).resize.put(disk='rootfs', size=disksize)
    
    interfaces = hostresource.properties[INTERFACES]
    for interface in interfaces:
    	print interface
    print "LXC created"    	
    

def removehost(host):
	if exists(host):
		container = Container.getContainer(HOST_CONTAINER)
		container.deleteResource(host)
		print "Removed host"
	else:
		print "Host not found"


def addControlPlaneIP(host, interface):
    """ Creates control plane ip from host id and adds it to host template"""
    container = Container.getContainer(HOST_CONTAINER)

    if exists(host):
        hostresource = container.loadResource(host)
        if interface in hostresource.properties:
            raise ValueError("Interface is already configured")

        hostid = hostresource.properties[HOSTID]
        cpoctet = str(hostid)
        netmask = str(CONTROLPLANE_NETMASK)
        cpip = CONTROLPLANE_PREFIX+cpoctet+"/"+netmask

        hostresource.properties[INTERFACES].append(interface)
        hostresource.properties[interface] = cpip

        container.saveResource(hostresource)
        return hostresource

    else:
        raise ValueError("Host does not exist. Please create template first")


def addDataPlaneIP(host, interface, vlan):
    """ Creates data plane ip from host id, project and adds it to host template"""
    container = Container.getContainer(HOST_CONTAINER)

    if exists(host):
        hostresource = container.loadResource(host)
        if interface in hostresource.properties:
            raise ValueError("Interface is already configured")

        hostid = hostresource.properties[HOSTID]
        projectid = int(hostresource.properties[PROJECT])
        dpip=""
    
        if(vlan == DATAPLANE_VLAN4012):
            ifaceid = interface.strip(string.ascii_letters)
            interface_number = ifaceid.split(".")[0]
            dpip = DATAPLANE_PREFIX+str(interface_number)+"."+str(projectid)+"."+str(hostid)
        elif (vlan == DATAPLANE_VLAN4020):
            ifaceid = interface.strip(string.ascii_letters)
            interface_number = int(ifaceid.split(".")[0])
            projectid += 100 #add 100 to project-id for vlan 4020
            dpip = DATAPLANE_PREFIX+str(interface_number)+"."+str(projectid)+"."+str(hostid)

        netmask = str(CONTROLPLANE_NETMASK)
        dpip = dpip + "/" + netmask

        hostresource.properties[INTERFACES].append(interface)
        hostresource.properties[interface] = dpip

        container.saveResource(hostresource)
        return hostresource

    else:
        raise ValueError("Host does not exist. Please create template first")



def addIP(host, interface, ipaddress):
    """ Adds interface and ipaddress to host template"""
    container = Container.getContainer(HOST_CONTAINER)

    if exists(host):
            
        hostresource = container.loadResource(host)
        if interface in hostresource.properties:
            raise ValueError("Interface is already configured")
        hostid = hostresource.properties[HOSTID]
        
        hostresource.properties[INTERFACES].append(interface)
        hostresource.properties[interface] = ipaddress

        container.saveResource(hostresource)
        return hostresource

    else:
        raise ValueError("Host does not exist. Please create template first")



def print_help():
    "Help message for tbhost utility"
    print "ESnet Testbed Host Utility"
    print "tbip <cmd> <cmds options>"
    print " Commands are:"
    print "\thelp"
    print "\t\tPrints this help."
    print "\tcreate"
    print "\t\tcreate <hostname> hypervisor <hypervisor> owner <owner> project <project> os <os> [id <id>]"
    print "\t\tCreates container template and gets an id for the container"
    print "\t\t<hostname> hostname of the container"
    print "\t\thypervisor <hypervisor> name of the hypervisor where the host is to be created. E.g.: star-tbn-4, 192.168.120.2"
    print "\t\towner <owner> owner's email address"
    print "\t\tproject <project> project-id. must be an integer"
    print "\t\tos <os> os template to be loaded - Values: centos-7-esnet, centos-7-dtn, debian-8-esnet, debian-8-dtn"
    print "\t\tOptional: id <id> id of the host if it was already created"
    print "\t\tExample usage: create mycontainer hypervisor nersc-tbn-4 owner sowmya@es.net project 120 os centos-7-esnet"
    print "\tbuildlxc"
    print "\t\tbuildlxc <hostname>"
    print "\taddif"
    print "\t\taddif <hostname> if <if_name> <ipaddress/netmask|auto_ip> [vlan <vlan>]"
    print "\t\tAssigns ip and adds interface to host template."
    print "\t\tauto_ip is allowed only for eth0 and for dataplane IP on VLAN 4012 and 4020"

if __name__ == '__main__':
    argv = sys.argv

    if len(argv) == 1:
        print_help()
        sys.exit()
    cmd = argv[1]
    if cmd == "help":
        print_help()
    elif cmd == 'create':
        if (len(argv)) < 11:
            print "ERROR: Argument mismatch"
            print_help()
        else:
            host = argv[2]

            if argv[3] == 'hypervisor':
                hypervisor = argv[4]
            else:

                print "ERROR: Argument mismatch"
                print_help()
                sys.exit()

            if argv[5] == 'owner':
                owner = argv[6]
            else:

                print "ERROR: Argument mismatch"
                print_help()
                sys.exit()

            if argv[7] == 'project':
                pid = argv[8]
                if pid < 0 or pid > 255:
                	print "Warning: Project value is greater than 255. This will lead to wrong Dataplane IP auto-generation"
            else:
                print "ERROR: Argument mismatch"
                print_help()
                sys.exit()

            if argv[9] == 'os':
                os = argv[10]
            else:
                print "ERROR: Argument mismatch"
                print_help()
                sys.exit()

            if len(argv)>11 and argv[11] == 'id':
                hostid = argv[12]
            try:
                if(len(argv)>11):
                    createHostTemplateWithId(host,hypervisor,owner,pid, hostid, os)
                    print "Host template created"
                else:
                    createHostTemplate(host,hypervisor,owner,pid, os)
                    print "Host template created" 
            except ValueError as e:
                print e                
    elif cmd == 'addif':
        auto_ip = False
        if (len(argv)) < 6:
            print "ERROR: Argument mismatch"
            print_help()
        else:
            host = argv[2]

            if argv[3] == 'if':
                interface = argv[4]
            else:
                print "ERROR: Expected interface"
                print_help()
            if argv[5] == 'auto_ip':
                auto_ip = True
            else:
                ipaddress = argv[5]
            vlan=None
            if len(argv)==8 and argv[6] == 'vlan':
                vlan=int(argv[7])
            print interface
            print host
            if interface == CONTROL_PLANE_INTERFACE and auto_ip:
                try:
                    hostresource = addControlPlaneIP(host,interface)
                    print "Interface\tIPAddress ",
                    print hostresource.properties[INTERFACES]
                    for inf in hostresource.properties[INTERFACES]:
                        print inf+"\t"+hostresource.properties[inf]
                except ValueError as e:
                    print e
            elif interface != CONTROL_PLANE_INTERFACE and vlan == DATAPLANE_VLAN4012 or vlan == DATAPLANE_VLAN4020:
                try:
                    hostresource = addDataPlaneIP(host,interface,vlan)
                    print "Interface\tIPAddress ",
                    print hostresource.properties[INTERFACES]
                    for inf in hostresource.properties[INTERFACES]:
                        print inf+"\t"+hostresource.properties[inf]
                except ValueError as e:
                    print e
            else:
                try:
                    hostresource = addIP(host, interface, ipaddress)
                    print "Interface\tIPAddress ",
                    print hostresource.properties[INTERFACES]
                    for inf in hostresource.properties[INTERFACES]:
                        print inf+"\t"+hostresource.properties[inf]
                except ValueError as e:
                    print e
    elif cmd == 'buildlxc':
    	hostname = argv[2]
    	buildlxc(hostname)
    elif cmd == 'removehost':
    	hostname = argv[2]
    	removehost(hostname)
    

    else:
        print_help()




