import socket, struct
from panda3d.core import Datagram

sock = socket.socket()
sock.connect(("127.0.0.1", 7100))

#custom = input("Enter custom message: ")

dg = Datagram()
dg.addUint64(1)                  # count
dg.addUint64(1000)             # dest channel
dg.addUint64(1234)             # sender
dg.addUint16(1)             # msg type
dg.addString("Hello, World!")    # payload
#dg.addString(custom)

payload = bytes(dg)
sock.send(struct.pack("<H", len(payload)))
sock.send(payload)
