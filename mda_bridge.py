"""
The exchange is a special source file since it is used as a pipe from the mail
delivery agent to the rest of the application.  This source is actually
executed potentially with the same permissions as the MDA and thus should be
minimalistic and not reference any other source from the photo frame
project.

By default a postfix server runs this application as nobody."""

import sys
import zmq

PATH = 'ipc:///home/application/local/sockets/photo_frame'

try:
    email = sys.stdin.read()

    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(PATH)
    socket.send(email)
    message = socket.recv()
except:
    pass

sys.exit(0)
