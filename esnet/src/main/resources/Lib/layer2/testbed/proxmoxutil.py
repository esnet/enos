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

""" This is a util module for proxmox. It has helper methods to set proxmox host, user and password"""

from net.es.netshell.api import Resource, Container
import getpass
import os

PROXMOX_CONTAINER = "proxmox"
USERRESOURCE = "user"
PRIMARY_HYPERVISOR = "primary_hypervisor"
HYPERVISORRESOURCE = "hypervisor"

DEFAULT_PORT = 8006

PROPERTIES_TYPE= "type"
PROPERTIES_HYPERVISOR = "hypervisor"
PROPERTIES_PORT = "port"
PROPERTIES_USER = "user"
PROPERTES_PASSWORD = "password"
PROPERTES_AUTHREALM = "authrealm"

PROPERTIES_OS = 'os'
PROPERTIES_OSTEMPLATE = 'ostemplate'

PROPERTIES="properties"


def setuser(username,password,authrealm):
    """ This method stores the username and password to be used on proxmox hypervisors """
    if(username != None and password != None):
        container = Container.getContainer(PROXMOX_CONTAINER)
        userresource = Resource(PROPERTIES_USER)
        userresource.properties[PROPERTIES_TYPE] = USERRESOURCE
        userresource.properties[PROPERTIES_USER] = username
        userresource.properties[PROPERTES_PASSWORD] = password
        userresource.properties[PROPERTES_AUTHREALM] = authrealm
        container.deleteResource(PROPERTIES_USER)
        container.saveResource(userresource)
    else:
        raise TypeError("Username/password cannot be None Type")

def clearuser():
    """ This method removes the username"""
    container = Container.getContainer(PROXMOX_CONTAINER)
    container.deleteResource(PROPERTIES_USER)

def listuser():
    """ This method returns users """
    container = Container.getContainer(PROXMOX_CONTAINER)
    user = container.loadResource(PROPERTIES_USER)
    return user

def setprimary(hypervisor):
    """ This method sets the primary hypervisor to be used. Only hypervisors that exist in the database can be added"""
    if(hypervisor != None):
        container = Container.getContainer(PROXMOX_CONTAINER)
        hresource = container.loadResource(hypervisor)

        if(hresource != None):
            primaryhypervisor = Resource(PRIMARY_HYPERVISOR)
            primaryhypervisor.properties[PROPERTIES_HYPERVISOR] = hresource.properties[PROPERTIES_HYPERVISOR]
            primaryhypervisor.properties[PROPERTIES_PORT] = hresource.properties[PROPERTIES_PORT]
            container.deleteResource(PRIMARY_HYPERVISOR)
            container.saveResource(primaryhypervisor)
        else:
            raise ValueError("Attempting to make a nonexistent hypervisor as primary. Please add the hypervisor using addhypervisor command")

    else:
        raise TypeError("Nonetype in hypervisor")


def listprimary():
    """ This method returns primary hypervisor """
    container = Container.getContainer(PROXMOX_CONTAINER)
    primary = container.loadResource(PRIMARY_HYPERVISOR)
    return primary


def clearprimary():
    """ This method clears primary hypervisor """
    container = Container.getContainer(PROXMOX_CONTAINER)
    primary = container.deleteResource(PRIMARY_HYPERVISOR)
    return primary


def addhypervisor(hypervisor, port):
    """ This method adds hypervisor to the database """
    if(hypervisor != None):
        container = Container.getContainer(PROXMOX_CONTAINER)
        hresource = Resource(hypervisor)
        hresource.properties[PROPERTIES_HYPERVISOR] = hypervisor
        hresource.properties[PROPERTIES_TYPE] = HYPERVISORRESOURCE
        if (port != None):
            hresource.properties[PROPERTIES_PORT] = port
        else:
            hresource.properties[PROPERTIES_PORT] = DEFAULT_PORT
        container.deleteResource(hypervisor)
        container.saveResource(hresource)
    else:
        raise TypeError("hypervisor is null")


def removehypervisor(hypervisor):
    """ This method removes the hypervisor"""
    if(hypervisor != None ):
        container = Container.getContainer(PROXMOX_CONTAINER)
        primary = container.loadResource(PRIMARY_HYPERVISOR)
        if(primary and primary.properties[PROPERTIES_HYPERVISOR] == hypervisor):
            raise ValueError(hypervisor+" is primary hypervisor. Clear primary before removing hypervisor")
        else:
            if(container.loadResource(hypervisor) != None):
                hresource = container.deleteResource(hypervisor)
            else:
                raise ValueError("Attempting to delete nonexistent Hypervisor")
    else:
        raise TypeError("Hypervisor cannot be None Type")

def listhypervisors():
    """ This method returns primary hypervisor """
    container = Container.getContainer(PROXMOX_CONTAINER)
    query={}
    key=PROPERTIES+"."+PROPERTIES_TYPE
    query[key] = HYPERVISORRESOURCE
    hypervisors = container.loadResources(query)
    return hypervisors

def addostemplate(os, ostemplate):
    """ This method adds ostemplate file location to the database """
    if(ostemplate != None):
        container = Container.getContainer(PROXMOX_CONTAINER)
        osresource = Resource(os)
        osresource.properties[PROPERTIES_TYPE] = PROPERTIES_OS
        osresource.properties[PROPERTIES_OS] = os
        osresource.properties[PROPERTIES_OSTEMPLATE] = ostemplate
        container.deleteResource(os)
        container.saveResource(osresource)
    else:
        raise TypeError("ostemplate is null")

def removeostemplate(os):
    """ This method removes the template"""
    if(os != None ):
        if(container.loadResource(os)):
            container.deleteResource(os)
        else:
            raise ValueError("Attempting to delete nonexistent Hypervisor")
    else:
        raise TypeError("OS cannot be None Type")

def listostemplates():
    """ This methodreturns a list of templates """
    container = Container.getContainer(PROXMOX_CONTAINER)
    query={}
    key=PROPERTIES+"."+PROPERTIES_TYPE
    query[key] = PROPERTIES_OS
    templates = container.loadResources(query)
    return templates

def getostemplate(os):
    """ This method returns the ostemplate for given os """
    container = Container.getContainer(PROXMOX_CONTAINER)
    template = container.loadResource(os)
    return template



def print_help():
    "Help message for proxmox management utility"
    print "ESnet Testbed proxmox utility"
    print "proxmoxutil <cmd> <cmds options>"
    print " Commands are:"
    print "\thelp"
    print "\t\tPrints this help."
    print "\tsetuser"
    print "\t\tsetuser <username> <authrealm>"
    print "\t\tAdds user to database"
    print "\tlistuser"
    print "\t\tLists users"
    print "\tclearuser"
    print "\t\tclearuser"
    print "\t\tRemoves user from database"
    print "\taddhypervisor"
    print "\t\taddhypervisor <hypervisor> port <port>"
    print "\t\tAdds hypervisor to database"
    print "\tlisthypervisors"
    print "\t\tList hypervisors"
    print "\tremovehypervisor"
    print "\t\tremovehypervisor <hypervisor>"
    print "\t\tRemoves hypervisor from database"
    print "\tsetprimary"
    print "\t\tsetprimary <hypervisor>"
    print "\t\tSets hypervisor as primary"
    print "\tlistprimary"
    print "\t\tList hypervisors"
    print "\tclearprimary"
    print "\t\tClears primary"
    print "\taddostemplate"
    print "\t\taddostemplate <os> template <template>"
    print "\t\tAdds os template to database"
    print "\tlisttemplate"
    print "\t\tList OS templates"
    print "\tremoveostemplate"
    print "\t\tremovehypervisor <os>"
    print "\t\tRemoves os template from database"


if __name__ == '__main__':
    argv = sys.argv

    if len(argv) == 1:
        print_help()
        sys.exit()
    cmd = argv[1]
    if cmd == "help":
        print_help()
    elif cmd == "setuser":
        if (len(argv)) != 4:
            print "ERROR: Argument mismatch"
            print_help()
        else:
            user = argv[2]
            authrealm = argv[3]
            password = getpass.getpass()

        
            try:
                setuser(user,password,authrealm)
                print "Username and password saved"
            except TypeError:
                print "Null values not allowed in username and password"
    elif cmd == "listuser":
        user = listuser()
        if user:
            print user
        else:
            print "No users found!"
    elif cmd == "clearuser":
        clearuser()
        print "User removed"
    elif cmd == "addhypervisor":
        if (len(argv)) < 3:
            print "ERROR: Argument mismatch"
            print_help()
        else:
            host = argv[2]
            port = DEFAULT_PORT
            if(len(argv)>3 and argv[3] == 'port'):
                try:
                    port = int(argv[4])
                except ValueError:
                    print 'ERROR: port must be integer'
                    print_help()
            try:
                addhypervisor(host,port)
                print "Hypervisor added"
            except ValueError:
                print "Hypervisor exists"
            except TypeError:
                print "Hypervisor cannot be null"
    elif cmd == "listhypervisors":
        hosts = listhypervisors()
        if hosts:
            print "Hypervisors\tPort"
            for host in hosts:
                print host.properties[PROPERTIES_HYPERVISOR],
                print '\t',
                print host.properties[PROPERTIES_PORT]
        else:
            print "No hypervisors found!"
    elif cmd == "removehypervisor":
        if (len(argv)) != 3:
            print "ERROR: Argument mismatch"
            print_help()
        else:
            hypervisor = argv[2]
            try:
                removehypervisor(hypervisor)
                print "Hypervisor "+hypervisor+" removed"
            except TypeError:
                print "ERROR: Please specify hypervisor"
            except ValueError:
                print "Hypervisor does not exist in database"
    elif cmd == "setprimary":
        if (len(argv))<3:
            print "ERROR: Argument mismatch"
            print_help()
        else:
            host = argv[2]          
            try:
                setprimary(host)
                print host+" is now primary hypervisor"
            except TypeError:
                print "Hypervisor is null. Please specify a hypervisor"
            except ValueError:
                print "Trying to add nonexistent hypervisor. Please add hypervisor using addhypervisor command"
                print_help()
    elif cmd == "listprimary":
        host = listprimary()
        if host:
            print "Primary Hypervisor: "+host.properties[PROPERTIES_HYPERVISOR]
            print "Port: "+str(host.properties[PROPERTIES_PORT])
        else:
            print "No hypervisors found!"
    elif cmd == "clearprimary":
        clearprimary()
        print "Primary hypervisor cleared"
    elif cmd == "addostemplate":
        if (len(argv)) < 5:
            print "ERROR: Argument mismatch"
            print_help()
        else:
            os = argv[2]
            if argv[3] == 'template':
                ostemplate = argv[4]
            else:                    
                print 'ERROR: Expected template'
                print_help()
            try:
                addostemplate(os,ostemplate)
                print "OS Template added"
            except TypeError:
                print "Hypervisor cannot be null"
    elif cmd == "listostemplates":
        ostemplates = listostemplates()
        if ostemplates:
            print "OS\t\tTEMPLATE FILE"
            for ostemplate in ostemplates:
                print ostemplate.properties[PROPERTIES_OS],
                print '\t',
                print ostemplate.properties[PROPERTIES_OSTEMPLATE]
        else:
            print "No templates found!"
    elif cmd == "removeostemplate":
        if (len(argv)) != 3:
            print "ERROR: Argument mismatch"
            print_help()
        else:
            os = argv[2]
            try:
                removeostemplate(os)
                print "Template "+os+" removed"
            except TypeError:
                print "ERROR: Please specify os"
            except ValueError:
                print "OS Template does not exist in database"
    else:
        print_help()







