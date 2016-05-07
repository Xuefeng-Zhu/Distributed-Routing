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
    POISON_MODE = True # Can override POISON_MODE here
    # DEFAULT_TIMER_INTERVAL = 15 # Can override this yourself for testing

    def __init__(self):
        """
        Called when the instance is initialized.

        You probably want to do some additional initialization here.
        """
        self.start_timer()  # Starts calling handle_timer() at correct rate
        self.route_table = {}
        self.min_route = {}
        self.port_latency = {}
        self.debug = False

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
            if self.debug:
                print packet
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
                self._forward_route(packet.destination, port)
        elif isinstance(packet, basics.HostDiscoveryPacket):
            if self.route_table.get(packet.src) is None:
                self.route_table[packet.src] = {}
            self.route_table[packet.src][
                port] = (self.port_latency[port], None)
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

    def _forward_route(self, destination, in_port=None):
        port, latency = self._get_min_latency(self.route_table[destination])
        route_packet = basics.RoutePacket(destination, latency)
        if port is not None:
            if in_port is None or port != self.min_route.get(destination):
                self.send(route_packet, port, flood=True)

            self.min_route[destination] = port

            if port is not None and port == in_port and self.POISON_MODE:
                self._send_poison(destination, port)

    def _get_min_latency(self, latencies):
        current_time = api.current_time()
        m_port = None
        m_latency = INFINITY
        for port, (latency, timer) in latencies.items():
            if timer is not None and current_time - timer > TIMEOUT:
                del latencies[port]
                continue

            if latency < m_latency:
                m_port = port
                m_latency = latency

        return m_port, m_latency

    def _send_poison(self, destination, port):
        poison_packet = basics.RoutePacket(destination, INFINITY)
        poison_packet.outer_color = [2,2,2,1]
        poison_packet.inner_color = [2,2,2,1]
        self.send(poison_packet, port)
