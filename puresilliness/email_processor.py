import email
import gevent.monkey
import os
import signal
import sys
import traceback
import uuid

gevent.monkey.patch_all()

import zmq.green as zmq

SOCKET_PATH = 'ipc:///home/application/local/sockets/photo_frame'
FILESTORE_PATH = '/home/application/local/filestore'


def shutdown():
    """A simple function to process a shutdown request from gevent."""
    sys.exit(0)


if __name__ == "__main__":
    gevent.signal(signal.SIGINT, shutdown)

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(SOCKET_PATH)
    if SOCKET_PATH.startswith('ipc://'):
        # make sure to chmod g+s the directory you are using for the ipc socket
        # so the ipc file will have the proper group
        os.chmod(SOCKET_PATH.replace('ipc://', ''), 0770)

    while True:
        message_string = socket.recv()

        try:
            email_message = email.message_from_string(message_string)
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type and content_type.startswith('image/'):
                    #print(part)
                    filename = uuid.uuid1()
                    with open(os.path.join(
                            os.sep, FILESTORE_PATH,
                            filename.hex), 'w') as file:
                        file.write(part.get_payload(None, True))
        except:
            print("error - {0}".format(sys.exc_info()[0]))
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(
                exc_type, exc_value, exc_traceback)
            print(''.join('!! ' + line for line in lines))

        socket.send("ack")
