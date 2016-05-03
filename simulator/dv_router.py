"""
Your awesome Distance Vector router for CS 168
"""

import sim.api as api
import sim.basics as basics


# We define infinity as a distance of 16.
INFINITY = 16


class DVRouter (basics.DVRouterBase):
    # NO_LOG = True # Set to True on an instance to disable its logging
    # POISON_MODE = True # Can override POISON_MODE here
    # DEFAULT_TIMER_INTERVAL = 5 # Can override this yourself for testing

    def __init__(self):
        """
        Called when the instance is initialized.

        You probably want to do some additional initialization here.
        """
        self.start_timer()  # Starts calling handle_timer() at correct rate
        self.route_table = {}
        self.port_latency = {}

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.

        The port attached to the link and the link latency are passed in.
        """
        self.port_latency[port] = latency

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.

        The port number used by the link is passed in.
        """
        del self.port_latency[port]
        for latencies in self.route_table.values():
            if port in latencies:
                del latencies[port]
        self.handle_timer()

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.

        packet is a Packet (or subclass).
        port is the port number it arrived on.

        You definitely want to fill this in.
        """
        #self.log("RX %s on %s (%s)", packet, port, api.current_time())
        if isinstance(packet, basics.RoutePacket):
            if self.route_table.get(packet.destination) is None:
                self.route_table[packet.destination] = {}
            latency = min(INFINITY,
                          self.port_latency.get(port, 16) + packet.latency)
            self.route_table[packet.destination][port] = latency
            self.handle_timer()
        elif isinstance(packet, basics.HostDiscoveryPacket):
            if self.route_table.get(packet.src) is None:
                self.route_table[packet.src] = {}
            self.route_table[packet.src][
                port] = self.port_latency.get(port, INFINITY)
            self.handle_timer()
        else:
            # Totally wrong behavior for the sake of demonstration only: send
            # the packet back to where it came from!
            out_port, _ = self._get_min_latency(
                self.route_table.get(packet.dst, {}))
            if out_port is None:
                self.send(packet, port, flood=True)
            else:
                self.send(packet, out_port)

    def handle_timer(self):
        """
        Called periodically.

        When called, your router should send tables to neighbors.  It also might
        not be a bad place to check for whether any entries have expired.
        """
        for destination, latencies in self.route_table.items():
            port, latency = self._get_min_latency(latencies)
            route_packet = basics.RoutePacket(destination, latency)
            self.send(route_packet, port, flood=True)

    def _get_min_latency(latencies):
        m_port = None
        m_latency = INFINITY
        for port, latency in latencies.items():
            if latency <= m_latency:
                m_port = port
                m_latency = latency
        return m_port, m_latency
