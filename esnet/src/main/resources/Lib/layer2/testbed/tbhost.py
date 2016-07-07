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

PROPERTIES_CPULIMIT = 'cpulimit'
PROPERTIES_CPUUNITS = 'cpuunits'
PROPERTIES_STORAGE='storage'
PROPERTIES_MEMORY='memory'
PROPERTIES_SWAP='swap'
PROPERTIES_DISK='disk'

CONTROLPLANE_PREFIX = '192.168.120.'
CONTROLPLANE_NETMASK = 24
CONTROLPLANE_VLAN = 2

CONTROL_PLANE_INTERFACE = 'eth0'

DATAPLANE_VLAN4012 = 4012
DATAPLANE_VLAN4020 = 4020
DATAPLANE_PREFIX = '10.'
DATAPLANE_NETMASK = 24

CPULIMIT = 0
CPUUNITS=1024
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
        hostresource.properties[PROPERTIES_CPULIMIT] = CPULIMIT
        hostresource.properties[PROPERTIES_CPUUNITS] = CPUUNITS
        hostresource.properties[PROPERTIES_STORAGE] = STORAGE
        hostresource.properties[PROPERTIES_MEMORY] = MEMORY
        hostresource.properties[PROPERTIES_SWAP] = SWAP
        hostresource.properties[PROPERTIES_DISK] = DISK

        #commenting out unitl lxc code is integrated
        if os and os != "unknown":
        	ostemplate = proxmoxutil.getostemplate(os)
        	if ostemplate is None:
        		raise ValueError("OS Template does not exist. Please configure os template using proxmoxutil")
        	else:
        		hostresource.properties[PROPERTIES_OSTEMPLATE] = ostemplate.properties[PROPERTIES_OSTEMPLATE]
        else:
        	hostresource.properties[PROPERTIES_OSTEMPLATE] = "unknown"

        hostresource.properties[INTERFACES] = []
        print "Creating host template for %s with id %s" %(host, str(hostid))
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
    
    hostname = hostresource.properties[HOSTNAME]  		
    vmid = int(hostresource.properties[HOSTID])
    ostemplate = str(hostresource.properties[PROPERTIES_OSTEMPLATE])
    cpulimit = int(hostresource.properties[PROPERTIES_CPULIMIT])
    cpuunits = int(hostresource.properties[PROPERTIES_CPUUNITS])
    memory = int(hostresource.properties[PROPERTIES_MEMORY])
    swap = int(hostresource.properties[PROPERTIES_SWAP])
    storage = hostresource.properties[PROPERTIES_STORAGE]
    disk = int(hostresource.properties[PROPERTIES_DISK])    
    disksize="%dG"%(disk)    
    interfaces = hostresource.properties[INTERFACES]
    
    i=0
    netconfig = dict()
    for interface in interfaces:
    	print "Configuring %s" %interface    	
    	netconfig["net"+str(i)] = hostresource.properties[interface]
    	i=i+1
    	
    print "Building LXC with the following parameters:"
    print "Vmid: %d" %vmid
    print "Template: %s" %ostemplate
    print "Cpu Limit: %d" %cpulimit
    print "Cpu Units: %d" %cpuunits
    print "Memory: %d" %memory
    print "Swap: %d" %swap
    print "Storage: %s" %storage
    print "Disk: %d" %disk 
    
    node.lxc.create(vmid=vmid, hostname=hostname, ostemplate=ostemplate, password=DEFAULT_PASSWORD, cpuunits=cpuunits, cpulimit=cpulimit, memory=memory, swap=swap, **netconfig)
    print "Creating LXC....."
    time.sleep(30)
    
    print "Resizing rootfs"	
    node.lxc(vmid).resize.put(disk='rootfs', size=disksize)
    time.sleep(30)
    print "LXC created"    
    
    
    
def rebuildlxc(host):
    """ Creates lxc in proxmox using given hostresource configuration """
    
    #check if container is running and ask user to stop it
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
    
    hostname = hostresource.properties[HOSTNAME]  		
    vmid = int(hostresource.properties[HOSTID])
    memory = int(hostresource.properties[PROPERTIES_MEMORY])
    swap = int(hostresource.properties[PROPERTIES_SWAP])
    interfaces = hostresource.properties[INTERFACES]
    
    i=0
    netconfig = dict()
    for interface in interfaces:
    	print "Configuring %s" %interface    	
    	netconfig["net"+str(i)] = hostresource.properties[interface]
    	i=i+1
    	
    print "Reconfiguring LXC with the following parameters:"
    print "Vmid: %d" %vmid
    print "Memory: %d" %memory
    print "Swap: %d" %swap
    
    node.lxc(vmid).config.put(memory=memory, swap=swap, **netconfig)
    print "Reconfiguring LXC....."
    time.sleep(30)
    
def deletelxc(host):
    """ Deletes lxc in proxmox using given hostresource configuration """
    
    #check if container is running and ask user to stop it
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
    vmid = int(hostresource.properties[HOSTID])
    
    proxmox = ProxmoxAPI(hypervisor, user=puser, password=password, verify_ssl=False)
    node = proxmox.nodes(hostresource.properties[HYPERVISOR])
    print "Deleting container"
    
    node.lxc(vmid).delete()
    time.sleep(30)
    print "Deleted container"
    
def startlxc(host):
    """ Start lxc in proxmox using given hostresource configuration """
    
    #check if container is running and ask user to stop it
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
    print "Starting  container"
    node.lxc(vmid).status.start.post()
    time.sleep(30)
    print "Started container"
    
def stoplxc(host):
    """ Stop lxc in proxmox using given hostresource configuration """
    
    #check if container is running and ask user to stop it
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
    print "Stopping  container"
    node.lxc(vmid).status.stop.post()
    time.sleep(30)
    print "Stopped  container"
    
def removehost(host):
	if exists(host):
		container = Container.getContainer(HOST_CONTAINER)
		hostresource = container.loadResource(host)
		hostid = str(hostresource.properties[HOSTID])
		idmanager.remove(hostid)	
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

        return addIP(host, interface, cpip, CONTROLPLANE_VLAN)

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

        return addIP(host, interface, dpip, vlan)

    else:
        raise ValueError("Host does not exist. Please create template first")



def addIP(host, interface, ipaddress, vlan):
    """ Adds interface and ipaddress to host template"""
    container = Container.getContainer(HOST_CONTAINER)

    if exists(host):
            
        hostresource = container.loadResource(host)
        if interface in hostresource.properties:
            raise ValueError("Interface is already configured")
        hostid = hostresource.properties[HOSTID]
        
        ipconfig = 'name='+interface+',ip='+ipaddress+',tag='+str(vlan)
        
        hostresource.properties[INTERFACES].append(interface)
        hostresource.properties[interface] = ipconfig

        container.saveResource(hostresource)
        return hostresource

    else:
        raise ValueError("Host does not exist. Please create template first")
        

def modifyIP(host, interface, ipaddress, vlan, bridge):
    """ Edits interface and ipaddress to host template"""
    container = Container.getContainer(HOST_CONTAINER)

    if exists(host):
            
        hostresource = container.loadResource(host)
        hostid = hostresource.properties[HOSTID]
        
        ipconfig = 'name='+interface+',bridge='+bridge+',ip='+ipaddress+',tag='+str(vlan)
        if interface in hostresource.properties:
            raise ValueError("Interface is already configured")
        else:
        	hostresource.properties[INTERFACES].append(interface)
               
        hostresource.properties[interface] = ipconfig

        container.saveResource(hostresource)
        return hostresource

    else:
        raise ValueError("Host does not exist. Please create template first")

def addbr(host, interface, bridge):
    """ Adds bridge to host template"""
    container = Container.getContainer(HOST_CONTAINER)

    if exists(host):
            
        hostresource = container.loadResource(host)
        if interface in hostresource.properties:
        	ipconfig = hostresource.properties[interface]
        	ipconfig += ",bridge="+bridge
        	hostresource.properties[interface] = ipconfig
        	container.saveResource(hostresource)
        	return hostresource
        else:
        	raise ValueError("Interface does not exist. Please create interface first")

    else:
        raise ValueError("Host does not exist. Please create template first")
        

def addstorage(host, size):
    """ Adds storage to host template"""
    container = Container.getContainer(HOST_CONTAINER)
    if exists(host):
    	hostresource = container.loadResource(host)
    	hostresource.properties[PROPERTIES_DISK] = size
    	container.saveResource(hostresource)
    	return hostresource
    else:
        raise ValueError("Host does not exist. Please create template first")
        
def addcpu(host, cpuunits, cpulimit):
    """ Adds storage to host template"""
    container = Container.getContainer(HOST_CONTAINER)

    if exists(host):
            
        hostresource = container.loadResource(host)
        hostresource.properties[PROPERTIES_CPUUNITS] = cpuunits
        hostresource.properties[PROPERTIES_CPULIMIT] = cpulimit
        container.saveResource(hostresource)
        return hostresource
    else:
        raise ValueError("Host does not exist. Please create template first")
        
def addmemory(host, memory, swap):
    """ Adds memory to host template"""
    container = Container.getContainer(HOST_CONTAINER)

    if exists(host):         
        hostresource = container.loadResource(host)
        hostresource.properties[PROPERTIES_MEMORY] = memory
        hostresource.properties[PROPERTIES_SWAP] = swap
        container.saveResource(hostresource)
        return hostresource
    else:
        raise ValueError("Host does not exist. Please create template first")
        

def listhostdetails(host):
    """ Adds memory to host template"""
    container = Container.getContainer(HOST_CONTAINER)

    if exists(host):         
        hostresource = container.loadResource(host)
        print "HostProperty\t\tValue"
        for key in hostresource.properties:
        	print "%s\t\t%s" %(key, hostresource.properties[key])
        return hostresource
    else:
        raise ValueError("Host does not exist")

def print_help():
    "Help message for tbhost utility"
    print "ESnet Testbed Host Utility"
    print "tbhost <cmd> <cmds options>"
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
    print "\taddif"
    print "\t\taddif <hostname> if <if_name> <ipaddress/netmask|auto_ip> [vlan <vlan>]"
    print "\t\tAssigns ip and adds interface to host template."
    print "\t\tauto_ip is allowed only for eth0 and for dataplane IP on VLAN 4012 and 4020"
    print "\taddbr"
    print "\t\taddbr <hostname> if <if_name> br <bridge>"
    print "\t\tAssigns bridge to interface and saves to host template."
    print "\tmodify"
    print "\t\tmodify <hostname> memory <memory> swap <swap>"
    print "\t\tModify memory and swap."
    print "\tmodify"
    print "\t\tmodify <hostname> if <interface> ip <ipaddress/netmask> vlan <vlan> br <bridge>"
    print "\t\tModify interface."
    print "\taddcpu"
    print "\t\taddcpu <hostname> cpulimit <cpulimit> cpuunits <cpuunits>"
    print "\t\tAdd cpu parameters. This method can be run only on a new container." 
    print "\taddstorage"
    print "\t\taddstorage <hostname> size <disksize> "
    print "\t\tAdd storage parameters. This method can be run only on a new container." 
    print "\tbuildlxc"
    print "\t\tbuildlxc <hostname>"
    print "\t\tCreates container in proxmox"
    print "\trebuildlxc"
    print "\t\trebuildlxc <hostname>"
    print "\t\tCan reconfigure lxc. (Memory and interface only)>"
    print "\tstartlxc"
    print "\t\tstartlxc <hostname>"
    print "\t\tStarts LXC"
    print "\tstoplxc"
    print "\t\tstoplxc <hostname>"
    print "\t\tStops LXC"
    print "\tremovehost"
    print "\t\tremovehost <hostname>"
    print "\t\tDeletes LXC and removes entry from database"
    print "\tlist"
    print "\t\tlist <hostname>"
    print "\t\tLists lxc details"


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
                pid = int(argv[8])
                if pid > 255:
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
                    hostresource = addIP(host, interface, ipaddress, vlan)
                    print "Interface\tIPAddress ",
                    print hostresource.properties[INTERFACES]
                    for inf in hostresource.properties[INTERFACES]:
                        print inf+"\t"+hostresource.properties[inf]
                except ValueError as e:
                    print e
    elif cmd == 'addbr':
    	if (len(argv)) < 6:
            print "ERROR: Argument mismatch"
            print_help()
        else:
            host = argv[2]
    	if argv[3] == 'if':
        	interface = argv[4]
        if argv[5] == 'br':
        	bridge = argv[6]
        	addbr(host, interface, bridge)
        	print "Added interface %s to bridge %s on host %s" %(interface, bridge, host)
        else:
        	print "Bridge name missing"      	
    elif cmd == 'modify':
    	if (len(argv)) < 6:
            print "ERROR: Argument mismatch"
            print_help()
        else:
            host = argv[2]
            if argv[3] == 'memory':
    	    	memory = argv[4]
    	    	if argv[5] == 'swap':
        			swap = argv[6]
        			addmemory(host,memory,swap)
        			print "Added memory: %s, swap: %s for %s" %(memory, swap, host)
    	    	else:
    	    		print_help()
    	    		sys.exit(1)
    	    elif argv[3] == 'if':
        		interface = argv[4]
        		if argv[5] == 'ip':
        			ip = argv[6]
        		if argv[7] == 'vlan':
        			vlan = argv[8]
        		if argv[9] == 'br':
        			br = argv[10]
        			modifyIP(host,interface,ip,vlan,br)       
    elif cmd == 'addcpu':
    	if (len(argv)) < 6:
            print "ERROR: Argument mismatch"
            print_help()
        else:
            host = argv[2]
            if argv[3] != 'cpulimit':
            	print_help()
            	sys.exit(1)
            	
            cpulimit = int(argv[4])
            if argv[5] != 'cpuunits':
        		print_help()
        		sys.exit(1)
            cpuunits = int(argv[6])
            addcpu(host, cpuunits, cpulimit)
            print "Added cpuunits: %s, cpulimit: %s for %s" %(cpuunits, cpulimit, host)

    elif cmd == 'addstorage':
    	if (len(argv)) < 5:
            print "ERROR: Argument mismatch"
            print_help()
        else:
            host = argv[2]
            if argv[3] == 'size':
        		disk = int(argv[4])
        		if(disk>10):
        			addstorage(host,disk)
        			print "Added storage: %sG for %s" %(disk, host)
        		else:
        			print "Please set disk value > 10"      		
    elif cmd == 'buildlxc':
    	hostname = argv[2]
    	buildlxc(hostname)
    elif cmd == 'rebuildlxc':
    	hostname = argv[2]
    	rebuildlxc(hostname)
    elif cmd == 'deletelxc':
    	hostname = argv[2]
    	deletelxc(hostname)
    elif cmd == 'startlxc':
    	hostname = argv[2]
    	startlxc(hostname)
    elif cmd == 'stoplxc':
    	hostname = argv[2]
    	stoplxc(hostname)
    elif cmd == 'removehost':
    	hostname = argv[2]
    	removehost(hostname)
    elif cmd == 'list':
    	hostname=argv[2]
    	listhostdetails(hostname)	
    else:
        print_help()




