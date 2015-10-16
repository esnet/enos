#
# ENOS, Copyright (c) 2015, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of any
# required approvals from the U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this software,
# please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov.
#
# NOTICE.  This software is owned by the U.S. Department of Energy.  As such,
# the U.S. Government has been granted for itself and others acting on its
# behalf a paid-up, nonexclusive, irrevocable, worldwide license in the Software
# to reproduce, prepare derivative works, and perform publicly and display
# publicly.  Beginning five (5) years after the date permission to assert
# copyright is obtained from the U.S. Department of Energy, and subject to
# any subsequent five (5) year renewals, the U.S. Government is granted for
# itself and others acting on its behalf a paid-up, nonexclusive, irrevocable,
# worldwide license in the Software to reproduce, prepare derivative works,
# distribute copies to the public, perform publicly and display publicly, and
# to permit others to do so.
#
from net.es.enos.perfsonar import EsmondClient
from net.es.enos.perfsonar import EsmondMeasurementFilter
from net.es.enos.perfsonar import EsmondDataFilter

# Configuration
baseUrl = "http://lbl-pt1.es.net:9085/esmond/perfsonar/archive"
timeRange=86400

# Retrieve measurements from esmond
c = EsmondClient()
f = EsmondMeasurementFilter()

# Retrieve all measurement sets and print them
measurements = c.retrieveEsmondMeasurements(baseUrl, f)
if measurements is not None:
    print "=== measurements on " + baseUrl + " ==="
    for m in measurements:
        print m.getToolName(), m.getSource(), m.getDestination()
        for e in m.getEventTypes():
            print " ", e.getEventType(), e.getBaseUri()

    print "==="

    # Now find iperf3 measurements
    df = EsmondDataFilter()
    df.setTimeRange(timeRange)
    print "=== iperf3 measurements ==="
    for m in measurements:
        if m.getToolName() == "bwctl/iperf3":
            print m.getToolName(), m.getSource(), m.getDestination()
            for e in m.getEventTypes():
                if e.getEventType() == "throughput":
                    ds = m.retrieveData(e, df)
                    print "---"
                    for d in ds:
                        print d.getTs(), d.getVal()

                    print "---"

    print "==="

    # Now find traceroute measurements
    df = EsmondDataFilter()
    df.setTimeRange(timeRange)
    print "=== traceroute measurements ==="
    for m in measurements:
        if m.getToolName() == "bwctl/tracepath,traceroute":
            print m.getToolName(), m.getSource(), m.getDestination()
            for e in m.getEventTypes():
                if e.getEventType() == "packet-trace":
                    ds = m.retrieveData(e, df)
                    if ds is not None:
                        print "---", len(ds), " paths ---"
                        for d in ds:
                            print d.getTs(), len(d.getVal()), "points"
                            for p in d.getVal():
                                print "  ", p.getTtl(), p.getIp(), p.getRtt()

                        print "---"

    print "==="

    # Finally...owamp measurements

    df = EsmondDataFilter()
    df.setTimeRange(timeRange)
    print "=== owamp measurements ==="
    for m in measurements:
        if m.getToolName() == "powstream":
            print m.getToolName(), m.getSource(), m.getDestination()
            for e in m.getEventTypes():
                if e.getEventType() == "histogram-owdelay":
                    ds = m.retrieveData(e, df)
                    if ds is not None:
                        print "---", len(ds), " samples ---"
                        for d in ds:
                            print d.getTs(), len(d.getVal()), "buckets", d.getVal()

                        print "---"

    print "==="
