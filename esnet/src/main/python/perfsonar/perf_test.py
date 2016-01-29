#!/usr/bin/python

#
# ESnet Network Operating System (ENOS) Copyright (c) 2015, The Regents
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
#
# Configures the initial ENOS deployment. Currently hard coded for ESnet deployment
#

import sys
import traceback
from net.es.enos.esnet import PerfSONARTester
from net.es.netshell.kernel.perfsonar import Bwctl
from net.es.netshell.rexec import SSHRemoteExecution

#Note: If argparse throws error related to sys.path or sys.prefix, please ensure both are set to the
# correct Jython path in your environment.


class PerfsonarTest():
    def __init__(self,testname):
        self.name = testname
        self.source = ""
        self.destination = ""
        self.testtype = "bwctl" #since that is the only test supported now
        self.interval = 0
        self.expires = 0
        self.initiator=""
        self.initiatorport=22
        self.initiatoruser='enos'
        self.keyfile=""

    def getname(self):
        return self.name

    def getsource(self):
        return self.source

    def getdestination(self):
        return self.destination

    def getinitiator(self):
        return self.initiator

    def getinitiatorport(self):
        return self.initiatorport

    def getkeyfile(self):
        return self.keyfile

    def gettesttype(self):
        return self.testtype

    def getinterval(self):
        return self.interval

    def getexpires(self):
        return self.expires
    
    def getinitiatoruser(self):
        return self.initiatoruser

    def setname(self,testname):
        if self.name is not None:
            raise Exception("Name already assigned")
        self.name = name
 
    def setsource(self,source):
        if self.source != "":
            print "Attempting to re-assign source"
            return
        self.source=source

    def setdestination(self,destination):
        if self.destination != "":
            print "Attempting to re-assign destination"
            return
        self.destination = destination
   
    def setinitiator(self,hostname):
        if self.initiator != "":
            print "Attempting to re-assign initiator"
            return
        self.initiator=hostname

    def setinitiatorport(self,port):
        self.initiatorport=port
 
    def setkeyfile(self,keyfile):
        self.keyfile=keyfile

    def setinitiatoruser(self,initiatoruser):
        self.initiatoruser=initiatoruser

def usage():
    print "\nperf_test help"
    print "\nperf_test showtesters"
    print "\nperf_test create <testname>"
    print "\nperf_test <testname> source <hostname>"
    print "\nperf_test <testname> destination <hostname>"
    print "\nperf_test <testname> initiator <hostname>"
    print "\nperf_test <testname> initiatorport <hostname>. Default: 22"
    print "\nperf_test <testname> initiatoruser <username>. Default: enos"
    print "\nperf_test <testname> keyfile <hostname>"
    print "\nperf_test <testname> show"
    print "\nperf_test <testname> run"
    print "\nperf_test <testname> runandsave"
    print "\n\n"    

def showtesters():
    print "\n*****PerfSONAR Testers*****\n"
    for tester in perf_testers:
        print tester

def create_test(testname):
    if testname in PSTests:
        print "%s exists" %testname
        return
    
    pstest = PerfsonarTest(testname)
    PSTests[testname]=pstest

def gettest(testname):
    return PSTests[testname]

def addport(test,hosttype,port):
    #TODO: check if host is present in perf_testers

    if test is None:
        print "Test not defined"
        return
    if hosttype == 'initiatorport':
        test.setinitiatorport(int(port))
    else:
        print "Unknown value. Accepted values: initiatorport"
        return

def addkeyfile(test,keyfile):
    if test is None:
        print "Test not defined"
        return
    test.setkeyfile(keyfile)
    return

def addusername(test,initiatoruser):
    if test is None:
        print "Test not defined"
        return
    test.setinitiatoruser(initiatoruser)
    return

def addhost(test,hosttype,hostname):
    #TODO: check if host is present in perf_testers

    if not hostname in perf_testers.keys() and hosttype != 'initiator':
        print "Please choose a valid perfsonar end point"
        return
    if test is None:
        print "Test not defined"
        return
    if hosttype == 'source':
        test.setsource(hostname)
    elif hosttype == 'destination':
        test.setdestination(hostname)
    elif hosttype == 'initiator':
        test.setinitiator(hostname)
    else:
        print "Unknown type of host. Accepted values: source|destination|initiator"
        return

def printtest(test):
    if test is None:
        print "Test not defined"
        return
    print "\n*****Test details*****\n"
    print "Test name: %s" %test.getname()
    print "Source: %s" %test.getsource()
    print "Destination: %s" %test.getdestination()
    print "\nInitiator: %s" %test.getinitiator()
    print "Initiator port: %d" %test.getinitiatorport()
    print "Initiator username: %s" %test.getinitiatoruser()
    print "\nKey file: %s" %test.getkeyfile()
 
def runtest(test): 
    if test is None:
        print "Test is not defined"
        return
    initiator = test.getinitiator() 
    initiatorport=test.getinitiatorport()
    source = test.getsource()
    destination = test.getdestination()
    
    if (source == '') or (destination == ''):
        print "Please define source/destination"
        return

    if initiator is None:
        print "Please specify initiator"
        return
    username=test.getinitiatoruser()
    keyfile=test.getkeyfile()
    ssh_client = SSHRemoteExecution(initiator, initiatorport,username, keyfile)
    ssh_client.setOut(sys.stdout)
    command = "bwctl -s " + source + "  -c " + destination +" -T iperf -t 10 -a 1 --parsable --verbose "
    ssh_client.setCommand(command)

    ret = ssh_client.loadKeys()
    ssh_client.exec()
    output_stream=ssh_client.getAccessRemoteOutputStream()

    print "Output"
    data = output_stream.read()
    while data != -1:
        sys.stdout.write(chr(data))
        data=output_stream.read()


def runandsavetest(test):
    if test is None:
        print "Test is not defined"
        return
    initiator = test.getinitiator()
    initiatorport=test.getinitiatorport()
    source = test.getsource()
    destination = test.getdestination()

    if (source == '') or (destination == ''):
        print "Please define source/destination"
        return

    if initiator is None:
        print "Please specify initiator"
        return
    username=test.getinitiatoruser()
    keyfile=test.getkeyfile()
    ssh_client = SSHRemoteExecution(initiator, initiatorport,username, keyfile)
    ssh_client.setOut(sys.stdout)
    user='gridftp'
    key='fedd4d4c49ed04e1124931bb0e581724f375259f'
    dburl='http://perfsonar-archive.es.net/esmond/archive'
    command = "bwctl -s " + source + "  -c " + destination +" -T iperf3 -t 10 -a 1 --parsable --verbose" +\
                     " |& " +\
                     "esmond-ps-pipe --user "+user +" --key "+key+ " -U "+dburl
    ssh_client.setCommand(command)
    ret = ssh_client.loadKeys()
    ssh_client.exec()
    output_stream=ssh_client.getAccessRemoteOutputStream()

    print "Output"
    data = output_stream.read()
    while data != -1:
        sys.stdout.write(chr(data))
        data=output_stream.read()
  
    getmetadata_command = 'esmond-ps-get-metadata --url http://perfsonar-archive.es.net/ --src '+source+' --dest'+ destination+'--output-format json'
    ssh_client.setCommand(getmetadata_command)    
        
    ssh_client.exec()
    output_stream=ssh_client.getAccessRemoteOutputStream()

    print "Output"
    data = output_stream.read()
    while data != -1:
        sys.stdout.write(chr(data))
        data=output_stream.read()

def main():

    if not 'PSTests' in globals():
        PSTests = {}
        globals()['PSTests'] = PSTests
   
    

    try:
        if (len(sys.argv)<2):
            usage()
            return

        command = sys.argv[1].lower()
        
        if command == 'create':
            if len(sys.argv)<3:
                print "Please specify test name"
                return
            testname = sys.argv[2].lower()
            create_test(testname)
        elif command == 'showtesters':
            showtesters()
        #TODO: a command to list all the tests
        elif command == 'help':
            usage()
        else:
            testname=sys.argv[1].lower()
            pstest = gettest(testname)
            if pstest is None:
                print "Test does not exist"
                return
            command = sys.argv[2].lower()
            if command == 'source' or command == 'destination' or command == 'initiator':
                host = sys.argv[3].lower()
                addhost(pstest,command,host)
            elif command == 'initiatorport':
                port = sys.argv[3]
                addport(pstest,command,port)
            elif command == 'keyfile':
                keyfile=sys.argv[3]
                keyfile= sys.netshell_root.toString()+keyfile
                addkeyfile(pstest,keyfile)
            elif command == 'initiatoruser':
                user = sys.argv[3]
                addusername(pstest,user)
            elif command == 'show':
                printtest(pstest)
            elif command == 'run':
                runtest(pstest)
            elif command == 'runandsave':
                runandsavetest(pstest)
            else:
                print "Unknown command"
                usage()

    except:
        usage()
        traceback.print_exc()
        raise Exception("Error running command")

if __name__ == '__main__':
    main()

