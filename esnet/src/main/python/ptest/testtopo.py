import sys
if sys.version.find("Java") == -1:
    from ptest.mininetobject import MininetSwitch as PSwitch
    from ptest.mininetobject import MininetSiteRouter as PSiteRouter
    from ptest.mininetobject import MininetCoreRouter as PCoreRouter
    from ptest.mininetobject import MininetHwSwitch as PHwSwitch
    from ptest.mininetobject import MininetHost as PHost
    from ptest.mininetobject import MininetPort as PPort
    from ptest.mininetobject import MininetLink as PLink
    from ptest.mininetobject import MininetSDNPop as PSDNPop
    from ptest.mininetobject import MininetVPN as PVPN
else:
    from ptest.pobject import PSwitch, PSiteRouter, PCoreRouter, PHwSwitch
    from ptest.pobject import PHost
    from ptest.pobject import PPort
    from ptest.pobject import PLink
    from ptest.pobject import PSDNPop
    from ptest.pobject import PVPN

class TestTopo:
    def __init__(self):
        self.switches = []
        self.hosts = []
        self.links = []
        self.switchIndex = 0
        self.hostIndex = 0
        self.wanIndex = 1000
        self.switchesDict = {}
        self.hostsDict = {}
        self.popsDict = {}
        # POP
        self.stitches = []
        # VPN
        self.vpns = {} # vpns[vid] = PVPN
        # should be overrided by customized topology
        # NOTE: since not connected to mininet yet,
        # any operation involved in addFlowMod or broadcast should be avoided here!
    def setController(self, controller):
        # should be overrided
        # addFlowMod could be invoked here
        # In addition, mininet script won't invoke this method,
        # so it's safe to use odl stuff
        for s in self.stitches:
            s[0].stitch(s[1], s[2])
    @staticmethod
    def create(type):
        if type == 2:
            return TestTopo2()
        elif type == 3:
            return TestTopo3()
        elif type == 4:
            return TestTopo4()
        elif type == 5:
            return TestTopo5()
        else:
            return TestTopo1()
    def nextMininetSwitchName(self):
        self.switchIndex += 1
        return 's%r' % self.switchIndex
    def nextMininetHostName(self):
        self.hostIndex += 1
        return 'h%r' % self.hostIndex
    def addHost(self, hostname):
        mininetName = self.nextMininetHostName()
        host = PHost(hostname, mininetName)
        self.addIndex(host)
        return host
    def addSite(self, sitename):
        mininetName = self.nextMininetSwitchName()
        site = PSiteRouter(sitename, mininetName)
        self.addIndex(site)
        return site
    def addSDNPop(self, popname, corename, hwname):
        mininetCoreName = self.nextMininetSwitchName()
        mininetHwName = self.nextMininetSwitchName()
        p = PSDNPop(popname, corename, hwname, mininetCoreName, mininetHwName)
        self.addIndex(p)
        return p
    def addSDNPopWithSite(self, popname, corename, hwname, sitename, hostnames):
        pop = self.addSDNPop(popname, corename, hwname)
        site = self.addSite(sitename)
        for hostname in hostnames:
            host = self.addHost(hostname)
            self.addLink(host, site)
        links = self.attachSite(site, pop)
        site.setWanPort(links[0].getPort(0))
        return (pop, site)
    def attachSite(self, site, pop):
        links = self.addLink(site, pop)
        pop.hw.setSitePort(links[2].getPort(1))
        return links
    def addLink(self, src, dst):
        """
        : return : links = (src:dst, src_core:src_hw, dst_core:dst_hw)
        """
        links = [None] * 3
        srcpop = None
        if isinstance(src, PSDNPop):
            srcpop = src
            src = src.core
        dstpop = None
        if isinstance(dst, PSDNPop):
            dstpop = dst
            dst = dst.core
        links[0] = PLink(src, dst)
        if srcpop:
            links[1] = PLink(srcpop.core, srcpop.hw)
            self.stitches.append((src, links[1].getPort(0), links[0].getPort(0)))
        if dstpop:
            links[2] = PLink(dstpop.core, dstpop.hw)
            self.stitches.append((dst, links[2].getPort(0), links[0].getPort(1)))
        for link in links:
            if link:
                self.addIndex(link)
        return links
    def addVPN(self, vid, vlan, participants):
        pops = map(lambda x : x[0], participants)
        vpn = PVPN(vid, pops)
        self.vpns[vid] = vpn
        for participant in participants:
            (pop, site, wanVlan) = participant
            site.addVlan(vlan, wanVlan)
            pop.hw.addVPN(wanVlan, vpn)
    def connectPops(self, pop1, pop2):
        links = self.addLink(pop1, pop2)
        self.wanIndex += 1
        for link in links:
            link.addVlan(self.wanIndex)
        pop1.hw.addPopPort(pop2, links[1].getPort(1))
        pop2.hw.addPopPort(pop1, links[2].getPort(1))
    def addIndex(self, inst):
        if isinstance(inst, PHost):
            self.hostsDict[inst.name] = inst
            self.hostsDict[inst.mininetName] = inst
            self.hosts.append(inst)
        elif isinstance(inst, PSwitch):
            self.switchesDict[inst.name] = inst
            self.switchesDict[inst.mininetName] = inst
            self.switches.append(inst)
        elif isinstance(inst, PLink):
            self.links.append(inst)
        elif isinstance(inst, PSDNPop):
            self.addIndex(inst.core)
            self.addIndex(inst.hw)
            self.popsDict[inst.name] = inst
    def getHost(self, hostname):
        if not hostname in self.hostsDict:
            print "hostname %r not found in topo" % hostname
            return None
        return self.hostsDict[hostname]
    def getSwitch(self, switchname):
        if not switchname in self.switchesDict:
            print "switchname %r not found in topo" % switchname
            return None
        return self.switchesDict[switchname]
    def getPop(self, popname):
        if not popname in self.popsDict:
            print "popname %r not found in topo" % popname
            return None
        return self.popsDict[popname]
class TestTopo1(TestTopo):
    def __init__(self):
        """
        h1-s1-h2, simplest topology
        """
        TestTopo.__init__(self)
        h1 = PHost('dtn-1@lbl.gov', 'h1')
        s1 = PSwitch('lbl.gov', 's1')
        h2 = PHost('dtn-2@lbl.gov', 'h2')
        l1 = PLink(h1, s1)
        l2 = PLink(s1, h2)
        # add to the container so that mininet could build up
        self.switches.extend([s1])
        self.hosts.extend([h1, h2])
        self.links.extend([l1, l2])

class TestTopo2(TestTopo):
    def __init__(self):
        """
        h1-s1-s2-h2
        note: broadcast might be fail if there is a circle in the topo!
        eg.  s1
          s2-+--s3, a broadcast message will never end (s1->s2->s3->s1...)
        """
        TestTopo.__init__(self)
        h1 = self.addHost('dtn-1@lbl.gov')
        s1 = self.addSite('lbl.gov')
        self.attachHost(h1, s1)
        h2 = self.addHost('dtn-1@anl.gov')
        s2 = self.addSite('anl.gov')
        self.attachHost(h2, s2)
        link = PLink(s1, s2)
        self.links.append(link)
    def setController(self, controller):
        for sitename in ['lbl.gov', 'anl.gov']:
            s = self.getSwitch(sitename)
            s.addVlan(10, 11)
        for link in self.links:
            s0 = link.getNode(0)
            s1 = link.getNode(1)
            if isinstance(s0, PSiteRouter) and isinstance(s1, PSiteRouter):
                s0.setWanPort(link.getPort(0))
                s1.setWanPort(link.getPort(1))

class TestTopo3(TestTopo):
    def __init__(self):
        """
        h1-s1=s2
        h2-+
        """
        TestTopo.__init__(self)
        h1 = self.addHost('dtn-1@lbl.gov')
        h2 = self.addHost('dtn-2@lbl.gov')
        p = self.addSDNPop('lbl', 'lbl-mr2', 'lbl-tb-of-1')
        l1 = self.addLink(h1, p)
        l2 = self.addLink(h2, p)
    def setController(self, controller):
        TestTopo.setController(self, controller)
        hw = self.getSwitch('lbl-tb-of-1')
        hw.stitch(hw.getPort(1), hw.getPort(2))

class TestTopo4(TestTopo):
    def __init__(self):
        """
        h1-s1-s2---s5-s4-h2
              ||   ||
              s3   s6
        """
        TestTopo.__init__(self)
        h1 = self.addHost('dtn-1@lbl.gov')
        s1 = self.addSite('lbl.gov')
        self.addLink(h1, s1)
        p1 = self.addSDNPop('lbl', 'lbl-mr2', 'lbl-tb-of-1')
        l1 = self.attachSite(s1, p1)
        s1.setWanPort(l1.getPort(0))

        h2 = self.addHost('dtn-1@anl.gov')
        s2 = self.addSite('anl.gov')
        self.addLink(h2, s2)
        p2 = self.addSDNPop('star', 'star-cr5', 'star-tb-of-1')
        l2 = self.attachSite(s2, p2)
        s2.setWanPort(l2.getPort(0))

        self.connectPops(p1, p2)
        self.addVPN(12345, 10, [(p1, s1, 11), (p2, s2, 12)])

class TestTopo5(TestTopo):
    def __init__(self):
        """
        h4-s7 - s8 == s9
                / \
        h1-s1-s2---s5-s4-h3
        h2-+  ||   ||
              s3   s6
        """
        TestTopo.__init__(self)
        (p1, s1) = self.addSDNPopWithSite('lbl', 'lbl-mr2', 'lbl-tb-of-1', 'lbl.gov', ['dtn-1@lbl.gov', 'dtn-2@lbl.gov'])
        (p2, s2) = self.addSDNPopWithSite('star', 'star-cr5', 'star-tb-of-1', 'anl.gov', ['dtn-1@anl.gov'])
        (p3, s3) = self.addSDNPopWithSite('cern', 'cern-cr5', 'cern-tb-of-1', 'cern.ch', ['dtn-1@cern.ch'])
        self.connectPops(p1, p2)
        self.connectPops(p1, p3)
        self.connectPops(p2, p3)
        self.addVPN(1234, 10, [(p1, s1, 11), (p2, s2, 12), (p3, s3, 13)])
        self.addVPN(5678, 20, [(p1, s1, 21), (p2, s2, 22)])
    def setController(self, controller):
        TestTopo.setController(self, controller)
