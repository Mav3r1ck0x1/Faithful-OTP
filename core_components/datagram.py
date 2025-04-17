import struct

class Datagram:
    def __init__(self, data=None):
        self.buffer = bytearray(data) if data else bytearray()  # Initialize with data if provided, or an empty buffer


    def addUint8(self, value):
        self.buffer.extend(struct.pack("<B", value))

    def addUint64(self, value):
        self.buffer.extend(struct.pack("<Q", value))

    def addUint16(self, value):
        self.buffer.extend(struct.pack("<H", value))

    def appendData(self, data):
        self.buffer.extend(data)

    def get_bytes(self):
        """
        Returns the full datagram as a byte sequence.
        """
        return bytes(self.buffer)

    def getLength(self):
        return len(self.buffer)

    def getMessage(self):
        return self.buffer
    
    def __str__(self):
        # Return a string representation of the datagram (as string, assuming it's text data)
        try:
            return self.buffer.decode('utf-8')
        except UnicodeDecodeError:
            return "Non-UTF-8 data in datagram"

    def to_hex(self):
        # Return a readable hex string representation of the datagram's buffer
        return "Datagram Content (Hex): " + " ".join(f"{byte:02x}" for byte in self.buffer)

class DatagramIterator:
    def __init__(self, datagram):
        self.buffer = datagram.get_bytes()  # The datagram's byte sequence
        self.offset = 0  # To keep track of the current reading position in the buffer

    def getUint8(self):
        value = struct.unpack_from("<B", self.buffer, self.offset)[0]
        self.offset += 1
        return value

    def getUint16(self):
        value = struct.unpack_from("<H", self.buffer, self.offset)[0]
        self.offset += 2
        return value

    def getUint64(self):
        value = struct.unpack_from("<Q", self.buffer, self.offset)[0]
        self.offset += 8
        return value

    def getString(self):
        length = self.getUint16()  # Assuming strings are prefixed with their length (e.g., a 2-byte length field)
        value = self.buffer[self.offset:self.offset + length].decode("utf-8")
        self.offset += length
        return value

    def getBlob(self):
        length = self.getUint16()  # Assuming blobs are prefixed with their length (e.g., a 2-byte length field)
        value = self.buffer[self.offset:self.offset + length]
        self.offset += length
        return value

    def getRemainingBytes(self):
        return self.buffer[self.offset:]