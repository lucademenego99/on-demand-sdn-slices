#!/usr/bin/python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink


class MeshTopo(Topo):
    """
    Define a sample topology with 5 hosts and 5 switches.
    The topology is a mesh topology.
    """

    def __init__(self):
        # Initialize topology
        Topo.__init__(self)

        # Create template host, switch, and link
        
        host_config = dict(inNamespace=True)
        """Hosts configuration"""

        link_config = dict(bw=10)
        """Switch-Switch links configuration"""

        host_link_config = dict()
        """Host-Switch links configuration"""

        switches = []
        """List of switches"""

        hosts = []
        """List of hosts"""

        # Create switch nodes
        for i in range(5):
            sconfig = {"dpid": "%016x" % (i + 1)}
            switches.append(self.addSwitch("s%d" % (i + 1), **sconfig))

        # Create host nodes
        for i in range(5):
            hosts.append(self.addHost("h%d" % (i + 1), **host_config))

        # Add switch links
        for i in range(0, len(switches)):
            for j in range(i+1, len(switches)):
                self.addLink(switches[i], switches[j], **link_config)

        # Add host links
        for i in range(0, len(hosts)):
            self.addLink(hosts[i], switches[i], **host_link_config)


topos = {"meshtopo": (lambda: MeshTopo())}

if __name__ == "__main__":
    topo = MeshTopo()
    net = Mininet(
        topo=topo,
        switch=OVSKernelSwitch,
        build=False,
        autoSetMacs=True,
        autoStaticArp=True,
        link=TCLink,
    )
    controller = RemoteController("c1", ip="127.0.0.1", port=6633)
    net.addController(controller)
    net.build()
    net.start()
    CLI(net)
    net.stop()
