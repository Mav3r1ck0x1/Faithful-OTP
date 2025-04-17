import asyncio
from asyncio import StreamReader, StreamWriter
#from panda3d.core import Datagram
from core_components.faithful_logger import notify
import struct
from core_components.datagram import Datagram, DatagramIterator
from core_components import msgTypes


class AsyncMDClient:
    def __init__(self, reader, writer, md, logger):
        """
        Initializes the AsyncMDClient.

        :param reader: Asynchronous reader for receiving data from the connection.
        :param writer: Asynchronous writer for sending data through the connection.
        :param md: The message director instance to handle incoming datagrams.
        :param logger: Logger instance for logging warnings and other messages.
        """
        self.reader = reader
        self.writer = writer
        self.md = md
        self.logger = logger

    async def handle(self):
        """Handles the incoming datagrams."""
        while True:
            try:
                length_bytes = await self.reader.readexactly(2)
                length = struct.unpack("<H", length_bytes)[0]
                data = await self.reader.readexactly(length)
                dg = Datagram(data)
                #await self.md.handle_datagram(dg, self)
                await self.handle_datagram(dg)
            except (asyncio.IncompleteReadError, ConnectionResetError) as e:
                #logger_mdclient.warning("MDClient disconnected.")
                logger_mdclient = notify.new_category("MDClient")
                logger_mdclient.faithfulWarning(f"MDClient disconnected. Error: {e}")
                #self.logger.MDClient(f"MDClient disconnected. Error: {e}")
                break


    async def handle_datagram(self, dg):
        di = DatagramIterator(dg)

        count = di.getUint8()
        channels = [di.getUint64() for _ in range(count)]
        sender = di.getUint64()

        for _ in range(count):
            channel = di.getUint8()
            channels.append(channel)

        if count == 1 and channels[0] == msgTypes.CONTROL_MESSAGE:
            code = di.getuint16()

            if code == msgTypes.CONTROL_SET_CHANNEL:
                new_channel = di.getUint64()
                print(f"[CONTROL] code={code}, set channel to {new_channel}")
                self.channels.add(new_channel)
            
            elif code == msgTypes.CONTROL_REMOVE_CHANNEL:
                remove_channel = di.getUint64()
                print(f"[CONTROL] code={code}, remove channel {remove_channel}")
                self.channels.discard(remove_channel)  # Use discard to avoid KeyError if missing
            
            elif code == msgTypes.CONTROL_ADD_POST_REMOVE:
                blob = di.getBlob()
                self.postRemove.append(blob)
                print(f"[CONTROL] code={code}, added post-remove blob of size {len(blob)}, contents (string): {blob.decode('utf-8')}")
            
            elif code == msgTypes.CONTROL_SET_CON_NAME:
                self.connectionName = di.getString()
                print(f"[CONTROL] code={code}, set connection name to {self.connectionName}")

            elif code == msgTypes.CONTROL_SET_CON_URL:
                self.connectionURL = di.getString()
                print(f"[CONTROL] code={code}, set connection URL to {self.connectionURL}")
            else:
                raise NotImplementedError(f"Unknown CONTROL_MESSAGE code: {code}")
            
            print(self.connectionName, self.connectionURL, self.channels)

        else:
            sender = di.getUint64()
            code = di.getUint16()

            for client in self.md.clients:
                if client == self:
                    continue
                
                if client.channels.intersection(channels):
                    client.sendDatagram(dg)

            await self.md.otp.handle_message(channels, sender, code, Datagram(di.getRemainingBytes()))




    async def _read_exactly(self, length):
        data = b""
        while len (data) < length:
            chunk = await self.reader.read(length - len(data))
            if not chunk:
                raise asyncio.IncompleteReadError(data, length)
                data += chunk
            return data

    async def send_datagram(self, dg):
        """
        Serializes and sends a datagram to the server asynchronously.

        :param dg: The Datagram object to send.
        """
        try:
            # Serialize the datagram to bytes
            datagram_bytes = bytes(dg)
            # Send the length of the datagram followed by the datagram bytes
            self.writer.write(struct.pack("<H", len(datagram_bytes)) + datagram_bytes)
            await self.writer.drain()  # Ensure the data is sent before continuing
            self.logger.info(f"[AsyncMDClient] Sent datagram: {datagram_bytes}")
        except Exception as e:
            self.logger.error(f"[AsyncMDClient] Error sending datagram: {e}")
            await self.close()

    async def close(self):
        """Closes the connection."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self.logger.info("[AsyncMDClient] Connection closed.")

class AsyncCAClient:
    def __init__(self, ca, logger):
        """
        Initializes the AsyncCAClient.

        :param ca: The client agent instance to handle incoming data from the CA server.
        :param logger: Logger instance for logging messages.
        """
        self.ca = ca
        self.transport = None
        self.logger = logger

    def connection_made(self, transport):
        """Handles a new connection from a client."""
        self.transport = transport
        self.ca.clients.append(self)
        peername = transport.get_extra_info("peername")
        self.logger.info(f"[CA] Connection from {peername}")

    def data_received(self, data):
        """Handles incoming data from the CA server."""
        # Handle data from the server if needed (currently a placeholder)
        self.logger.debug(f"[CA] Data received: {data}")
        # Further CA protocol handling logic goes here

    def connection_lost(self, exc):
        """Handles when a connection is lost."""
        self.ca.clients.remove(self)
        self.logger.info("[CA] Client disconnected")

    async def send_datagram(self, dg):
        """
        Sends a datagram asynchronously to the client agent server.

        :param dg: The Datagram object to send.
        """
        try:
            # Serialize the datagram into bytes
            datagram_bytes = bytes(dg)
            # Send the length of the datagram followed by the datagram itself
            self.transport.write(struct.pack("<H", len(datagram_bytes)) + datagram_bytes)
            await self.transport.drain()  # Ensure data is sent before continuing
            self.logger.info(f"[AsyncCAClient] Sent datagram: {datagram_bytes}")
        except Exception as e:
            self.logger.error(f"[AsyncCAClient] Error sending datagram: {e}")
            self.transport.close()


class AsyncServer:
    def __init__(self, message_director, client_agent, logger):
        self.md = message_director
        self.ca = client_agent
        self.logger = logger


    async def handle_md_connection(self, reader: StreamReader, writer: StreamWriter):
        #self.logger.info("[MD] New MD client connected.")
        logger_mdclient = notify.new_category("MDClient")
        logger_mdclient.faithfulDebug("[MD] New MD client connected.")
        md_client = AsyncMDClient(reader, writer, self.md, self.logger)
        await md_client.handle()
    
    async def handle_ca_connection(self, reader: StreamReader, writer: StreamWriter):
        """Handle new connections to the CA server."""
        logger_caclient = notify.new_category("CAClient")
        logger_caclient.faithfulDebug("[CA] New CA client connected.")
        ca_client = AsyncCAClient(self.ca, self.logger)
        ca_client.connection_made(writer)  # Simulate connection being made

        await ca_client.send_datagram(Datagram("Hello CA"))  # Example of sending a datagram
        await asyncio.sleep(1)  # Wait a bit to ensure communication
    
    

        
        
    async def run(self):
        """Starts both MD and CA servers."""
        # Start MD socket
        logger_md = notify.new_category("MDServer")
        logger_md.faithfulDebug("Starting MD listener...")
        #self.logger.info("Starting MD listener...")
        self.md_server = await asyncio.start_server(
            self.handle_md_connection, "127.0.0.1", 7100
        )

        # Start CA socket
        logger_ca = notify.new_category("CAServer")
        logger_ca.faithfulDebug("Starting CA listener...")
        #self.logger.info("Starting CA listener...")
        self.ca_server = await asyncio.start_server(
            self.handle_ca_connection, "127.0.0.1", 7101
        )

        # Start both servers
        async with self.md_server, self.ca_server:
            logger_async = notify.new_category("AsyncServer")
            logger_async.faithfulDebug("AsyncServer is now listening.")
            await asyncio.gather(
                self.md_server.serve_forever(),
                self.ca_server.serve_forever()
            )



# Main entry point
if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Instantiate the MD and CA server components
    md = type("MessageDirector", (), {"clients": []})()  # Example placeholder for MD
    ca = type("ClientAgent", (), {"clients": []})()  # Example placeholder for CA

    # Start the async server
    async_server = AsyncServer(md, ca, logger)
    asyncio.run(async_server.start())
