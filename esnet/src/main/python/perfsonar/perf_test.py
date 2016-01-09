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

import argparse
import sys
import datetime
from net.es.enos.esnet import PerfSONARTester
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

    def getname(self):
        return self.name

    def getsource(self):
        return self.source

    def getdestination(self):
        return self.destination

    def gettesttype(self):
        return self.testtype

    def getinterval(self):
        return self.interval

    def getexpires(self):
        return self.expires

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


def usage():
    print "\nperf_test help"
    print "\nperf_test showtesters"
    print "\nperf_test create <testname>"
    print "\nperf_test <testname> source <hostname>"
    print "\nperf_test <testname> destination <hostname>"
    print "\nperf_test <testname> show"
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


def addhost(test,hosttype,hostname):
    #TODO: check if host is present in perf_testers
    if test is None:
        print "Test not defined"
        return
    if hosttype == 'source':
        test.setsource(hostname)
    elif hosttype == 'destination':
        test.setdestination(hostname)
    else:
        print "Unknown type of host. Accepted values: source|destination"
        return

def printtest(test):
    if test is None:
        print "Test not defined"
        return
    print "\n*****Test details*****\n"
    print "Test name: %s" %test.getname()
    print "Source: %s" %test.getsource()
    print "Destination: %s" %test.getdestination()
    
def main():

    if not 'PSTests' in globals():
        PSTests = {}
        globals()['PSTests'] = PSTests

    try:
        command = sys.argv[1].lower()
        
        if command == 'create':
            if len(sys.argv)<3:
                print "Please specify test name"
                return
            testname = sys.argv[2].lower()
            create_test(testname)
        elif command == 'showtesters':
            showtesters()
        elif command == 'help':
            usage()
        else:
            testname=sys.argv[1].lower()
            pstest = gettest(testname)
            command = sys.argv[2].lower()
            if command == 'source' or command == 'destination':
                host = sys.argv[3].lower()
                addhost(pstest,command,host)
            elif command == 'show':
                printtest(pstest)
            else:
                print "Unknown command"
                usage()

    except:
        usage()
        raise Exception("unable to parse command")

if __name__ == '__main__':
    main()

