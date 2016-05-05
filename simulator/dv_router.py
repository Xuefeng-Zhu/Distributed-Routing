"""
Your awesome Distance Vector router for CS 168
"""

import sim.api as api
import sim.basics as basics


# We define infinity as a distance of 16.
INFINITY = 16
TIMEOUT = 15


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
        for destination, latencies in self.route_table.items():
            if port in latencies:
                del latencies[port]
            self._forward_route(destination)

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
            latency = self.port_latency[port] + packet.latency
            if latency >= INFINITY:
                if port in self.route_table[packet.destination]:
                    del self.route_table[packet.destination][port]
                    self._forward_route(packet.destination)
            else:
                self.route_table[packet.destination][port] =\
                    (latency, api.current_time())
                self._forward_route(packet.destination)
        elif isinstance(packet, basics.HostDiscoveryPacket):
            if self.route_table.get(packet.src) is None:
                self.route_table[packet.src] = {}
            self.route_table[packet.src][
                port] = (self.port_latency.get[port], api.current_time())
            self._forward_route(packet.src)
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
        for destination in self.route_table:
            self._forward_route(destination)

    def _forward_route(self, destination):
        port, latency = self._get_min_latency(self.route_table[destination])
        route_packet = basics.RoutePacket(destination, latency)
        if port is not None:
            self.send(route_packet, port, flood=True)

    def _get_min_latency(latencies):
        current_time = api.current_time()
        m_port = None
        m_latency = INFINITY
        for port, (latency, timer) in latencies.items():
            if current_time - timer > TIMEOUT:
                del latencies[port]
                continue

            if latency < m_latency:
                m_port = port
                m_latency = latency

        return m_port, m_latency
