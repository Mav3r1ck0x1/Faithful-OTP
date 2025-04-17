import asyncio
import struct
import time
from core_components.message_director import MessageDirector
from core_components.faithful_logger import notify
from core_components.client_agent import ClientAgent
from core_components.network_server_async import AsyncServer

class faithfulOTP:
    def __init__(self, host='127.0.0.1', port=7100):
        self.our_channel = 0x1234ABCD
        self.control_channel = 1  # Common convention for MD control
        self.running = True
        self.otp = self  # self refers to the current instance of faithfulOTP, making it available as otp
        self.md = MessageDirector(self.otp)  # Pass self.otp to MessageDirector
        self.clients = {}

        # Handlers
        self.messageDirector = MessageDirector(self)
        self.clientAgent = ClientAgent(self)

        # Initialize AsyncServer with MD and CA handlers
        self.async_server = AsyncServer(self.md, self.clientAgent, notify)

    async def handle_message(self, channels, sender, code, datagram):
        logger = notify.new_category("MDClient")
        #logger.faithfulDebug(f"Channels: {channels}, Code: {code}, Datagram: {datagram}")
        logger.faithfulDebug(f"Channels: {channels}, Code: {code}, Datagram (Hex): {datagram.to_hex()}, Datagram (Str): {str(datagram)}")

        # Transmit received message from MD to other components
        self.clientAgent.handle(channels, sender, code, datagram)

    async def start_md(self):
        """Start the Message Director (MD) server asynchronously."""
        print("[*] Starting Message Director.")
        await self.md.start("127.0.0.1", 7100) 
        print("[*] Message Director started.")
        while not self.md.ready:
            await asyncio.sleep(5)
        print("[*] Message Director is ready.")

    async def connect_to_md(self):
        """Connect as a mock daemon asynchronously."""
        reader, writer = await asyncio.open_connection('127.0.0.1', 7100)
        print(f"[+] Connected to MD at 127.0.0.1:7100 as channel {hex(self.our_channel)}")
        await self.send_add_channel(self.our_channel, writer)

    async def send_add_channel(self, channel, writer):
        """Send add channel control message."""
        ADD_CHANNEL = 9001
        src = struct.pack(">Q", channel)
        dest = struct.pack(">Q", self.control_channel)
        body = struct.pack(">HHQ", ADD_CHANNEL, 0, channel)
        payload = src + dest + body
        packet = struct.pack(">H", len(payload)) + payload
        writer.write(packet)
        await writer.drain()
        print(f"[>] Sent add_channel control message for {hex(channel)}")

        """

    async def send_test_message(self, from_chan, to_chan, message_str, writer):
      
        src = struct.pack(">Q", from_chan)
        dest = struct.pack(">Q", to_chan)
        body = message_str.encode("utf-8")
        payload = src + dest + body
        packet = struct.pack(">H", len(payload)) + payload
        writer.write(packet)
        await writer.drain()
        print(f"[>] Sent test message from {hex(from_chan)} to {hex(to_chan)}")



        """



    async def receive_loop(self, reader):
        """Receive messages asynchronously."""
        try:
            while self.running:
                hdr = await reader.read(2)
                if not hdr:
                    break
                length = struct.unpack(">H", hdr)[0]
                payload = await reader.read(length)

                src = struct.unpack(">Q", payload[:8])[0]
                dest = struct.unpack(">Q", payload[8:16])[0]
                msg = payload[16:].decode('utf-8', errors='ignore')

                print(f"[<] Received from {hex(src)} to {hex(dest)}: {msg}")
        except asyncio.CancelledError:
            pass
        finally:
            print("[*] Connection closed.")

    async def run(self):
        """Run the server and client asynchronously."""
        await self.async_server.run()
        #await self.start_md()
        await self.connect_to_md()

        reader, writer = await asyncio.open_connection('127.0.0.1', 7100)
        #await self.send_test_message(from_chan=0x42, to_chan=self.our_channel, message_str="OTP handshake test OK.", writer=writer)
        
        # Start receiving messages asynchronously
        await self.receive_loop(reader)

if __name__ == "__main__":
    otp = faithfulOTP()
    asyncio.run(otp.run())
