"""
The MessageDirector (MD) is a core component for the OTP (Online Theme Park) Server

Role: Core message router between all other components. Acts as the central router for messages between all other components.
receives messages from other components, and routes them. A "message" is just an atomic/binary blob, with a maximum size of approximately 64kB, sent from one component to another. The routing is performed by means of routing identifiers called channels, where a message contains any number of destination channels, and most messages include a source channel. Each component tells the MD which channels it would like to subscribe to, and receives messages sent to its subscribed channels. In this manner, the messaging architecture of Astron is actually a very simple publish-subscribe system. 



Each message sent to/from the Message Director is:

A binary message: struct.pack(">H", len(data)) + data

The payload data is an atomic blob: it includes:

src_channel (8 bytes)

dest_channel (8 bytes)

optional payload (remaining bytes)

You must fully receive and interpret each message before acting on it — there's no partial handling. That’s what “atomic” implies here.


Every msg includes:

One or more destination channels (routing targs)

A source channel (where thr msg originated)

And a msgType identifier and payload


Components register which channels they wish to subscribe to. When a message is sent to those channels, the MD delivers it accordingly.


To keep the MessageDirector lightweight, it's stateless and does not inspect message contents nor care about the content or sematicss of the payload.

The MD only looks at routing metadata (channels) and forwards messages accordingly.


Functionality:

MD uses a publish-subscribe model via channels

Routes messages from source channel to destination channel(s)

Channel types:

Global: used for system-wide broadcasts
Range-based: used to isolate objects or players


The MD is used by ALL other components (CA, AI, DB, etc)


The message director is the simplest component.



        Handle a complete Panda3D Datagram:
         [uint8  count]
         [uint64 channel...] * count
         [uint64 sender]
         [uint16 msgType]
         [blob data...]
        
    



"""

import socket
import select
import struct
import asyncio

from panda3d.core import Datagram, DatagramIterator
from . import msgTypes
from core_components import network_manager
from core_components.faithful_logger import notify


import socket
import select
import struct
import asyncio

from panda3d.core import Datagram, DatagramIterator
from . import msgTypes
from core_components.faithful_logger import notify


class MDClient:
    """Represents one daemon connection to the Message Director."""

    def __init__(self, md, sock, addr):
        self.md = md                # back‑reference to MessageDirector
        self.sock = sock            # TCP socket
        self.addr = addr            # (ip, port)
        self.buffer = bytearray()   # raw recv buffer
        self.connectionName = ""    # optional human name
        self.connectionURL = ""     # optional URL
        self.channels = set()       # subscribed channels
        self.postRemove = []        # datagrams to replay on disconnect
        self.otp = md.otp

    def fileno(self):
        """Expose underlying socket for select()."""
        return self.sock.fileno()

    def onLost(self):
        """Called if connection is lost — replay any postRemove datagrams."""
        for raw in self.postRemove:
            self.onDatagram(Datagram(bytes(raw)))

    async def onData(self, data):
        """
        Buffer incoming bytes, process complete packets.
        Packet format: <uint16 length><raw datagram bytes>
        """
        self.buffer.extend(data)
        while len(self.buffer) >= 2:
            length = struct.unpack("<H", self.buffer[:2])[0]
            if len(self.buffer) < length + 2:
                break
            packet = bytes(self.buffer[2:2 + length])
            del self.buffer[:2 + length]
            await self.handle_datagram(Datagram(packet))

async def route_datagram(self, dg, channels, sender, di):
    code = di.getUint16()

    for client in self.clients:
        if client == sender:
            continue
        if client.channels.intersection(channels):
            client.sendDatagram(dg)

    await self.otp.handle_message(channels, sender, code, Datagram(di.getRemainingBytes()))

    def sendDatagram(self, dg):
        """
        Send a Panda3D Datagram over the socket:
        Prepend a little-endian uint16 length.
        """
        self.sock.send(struct.pack("<H", dg.getLength()))
        self.sock.send(bytes(dg))

    def close(self):
        """Clean up the connection."""
        try:
            self.sock.close()
        except:
            pass


class MessageDirector:
    """Main MD server: accepts MDClients, multiplexes I/O, routes Datagrams."""

    def __init__(self, otp):
        """
        otp: your OTP core instance with .handleMessage(channels, sender, code, dg)
        host/port: where to listen for MDClients
        """
        self.otp = otp  # Store the otp instance passed to MessageDirector
        #self.sock = socket.socket()
        #self.sock.bind(("127.0.0.1", 7100))  # Use localhost instead of 0.0.0.0
        #self.sock.listen(5)
        self.ready = False
        self.clients = []  # list of MDClient

    async def start(self, host, port):
        """Bind, listen, and enter main select loop."""
        self.sock = socket.socket()
        self.sock.bind((host, port))
        self.sock.listen(5)
        print(f"[MD] Listening on {host}:{port}")

        try:
            while True:
                # Prepare select list: server socket and all client sockets
                rlist = [self.sock] + [c.sock for c in self.clients]
                readable, _, _ = select.select(rlist, [], [])
                for s in readable:
                    if s is self.sock:
                        client_sock, addr = self.sock.accept()
                        client = MDClient(self.otp, client_sock, addr)  # Pass self.otp
                        self.clients.append(client)
                        print(f"[MD] New connection from {addr}")
                    else:
                        # Find corresponding MDClient
                        client = next((c for c in self.clients if c.sock is s), None)
                        if not client:
                            continue
                        try:
                            data = s.recv(4096)
                            if not data:
                                raise ConnectionResetError
                            await client.onData(data)
                        except ConnectionResetError:
                            print(f"[MD] Connection lost: {client.addr}")
                            client.onLost()
                            client.close()
                            self.clients.remove(client)
        except KeyboardInterrupt:
            print("[MD] Shutting down.")
        finally:
            self.stop()

    async def sendMessage(self, channels, sender, code, datagram):
        """
        Send a message *from* OTP core into the MD:
         channels: list of uint64
         sender: uint64
         code: uint16
         datagram: Panda3D Datagram (with body payload)
        """
        dg = Datagram()
        dg.addUint8(len(channels))
        for ch in channels:
            dg.addUint64(ch)
        dg.addUint64(sender)
        dg.addUint16(code)
        dg.appendData(datagram.getMessage())

        # Deliver to all subscribed clients
        for client in list(self.clients):
            if client.channels.intersection(channels):
                client.sendDatagram(dg)

        # Also give to OTP core if needed
        self.otp.handleMessage(channels, sender, code, datagram)

    def stop(self):
        """Close all connections and the listening socket."""
        for client in list(self.clients):
            client.close()
        if self.sock:
            self.sock.close()
        print("[MD] Shutdown complete.")


if __name__ == "__main__":
    # Example usage: run MD with a dummy OTP core
    class DummyOTP:
        def handleMessage(self, channels, sender, code, dg):
            print(f"[OTP] Received code={code} from {sender} channels={channels}")

    md = MessageDirector(DummyOTP())
    asyncio.run(md.start("127.0.0.1", 7100))







