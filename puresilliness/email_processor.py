import email
import email.utils
import gevent.monkey
import logging
import logging.config
import os
import signal
import sqlalchemy.orm.exc
import sys
import traceback
import uuid

from puresilliness.model import SESSION, User, AuthorizedEmail, Photo
import puresilliness.util

gevent.monkey.patch_all()

import zmq.green as zmq

EMAIL_PREFIX = 'photo+'
EMAIL_SUFFIX = '@puresilliness.com'
SOCKET_PATH = os.getenv(
    'SOCKET_PATH',
    'ipc:///home/application/local/sockets/photo_frame')
FILESTORE_PATH = os.getenv(
    'FILESTORE_PATH',
    '/home/application/local/filestore')
LOGGING_CONF = os.getenv(
    'LOGGING_CONF',
    '/home/application/local/conf/email_processor_logging.conf')


def shutdown():
    """A simple function to process a shutdown request via gevent.  This
    processer is run via a supervisor script that sends a signal to interrupt
    processing."""
    sys.exit(0)


def get_to_user(address, session):
    """Queries the database based on the email address suffix for the User
    row to get the user's id."""
    try:
        return session.query(User).filter(User.email_id == address).one()
    except sqlalchemy.orm.exc.MultipleResultsFound:
        LOG.error('There should never be multiple email mappings: {0}'
                  .format(address))
    except sqlalchemy.orm.exc.NoResultFound:
        LOG.debug('Email keyword wasn\'t found: {0}'.format(address))

    return None


def get_an_authorized_email(user, addresses, session):
    """Queries the list of froms(which should really just be one from) for
    an email that is authorized to send photos to a specific photo frame
    user."""
    try:
        return session.query(AuthorizedEmail.email).filter_by(
            id=User.id).filter(AuthorizedEmail.email.in_(addresses)).first()
    except:
        LOG.error("Unexpected exception in get_an_authorized_email")

    return None


def process_email_parts(user_id, authorized_email, email_message, session):
    """Processes the email body to pull out and save images in the email."""

    def process_part(part):
        """Internal method to process one part of the email that was identified
        as an image."""

        image_id = uuid.uuid1()
        photo = Photo(id=user_id, email=authorized_email,
                      photo_id=image_id)
        session.add(photo)
        session.commit()
        filename = '{0}-{1}'.format(user_id.hex, image_id.hex)
        with open(os.path.join(os.sep, FILESTORE_PATH, filename), 'w') as f:
            f.write(part.get_payload(None, True))

    try:
        count = 0
        for part in email_message.walk():
            content_type = part.get_content_type()
            if content_type and content_type.startswith('image/'):
                process_part(part)
                count += 1
        LOG.debug('Processed parts: {0}'.format(count))
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        LOG.error("Unexpected process_email_parts error - {0}".format(
            exc_type))
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        LOG.error(''.join('!! ' + line for line in lines))


def process_email(email_message):
    """Process an individual mail message and save photos as needed."""
    try:
        LOG.debug("-------------------------------------------------------")
        LOG.debug("Processing An Email:")
        email_message = email.message_from_string(message_string)
        session = SESSION()

        froms = email_message.get_all('from', [])
        if len(froms) < 1:
            return

        tos = email_message.get_all('to', [])
        if len(tos) < 1:
            return

        for t in tos:
            address = email.utils.parseaddr(t)[1]
            if(not address.startswith(EMAIL_PREFIX) or
               not address.endswith(EMAIL_SUFFIX)):
                continue

            address = address[len(EMAIL_PREFIX):-len(EMAIL_SUFFIX)]

            to_user = get_to_user(address, session)
            if not to_user:
                continue

            from_emails = []
            for f in froms:
                from_emails.append(email.utils.parseaddr(f)[1])

            from_auth = get_an_authorized_email(to_user, from_emails, session)
            if from_auth:
                from_auth = from_auth[0]
                LOG.debug('Found authorized pair: {0}:{1}'.format(
                    to_user.email_id, from_auth))
                process_email_parts(to_user.id, from_auth,
                                    email_message, session)
            else:
                LOG.debug('Email addresses are not authorized')

    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        LOG.error("Unexpected process_email error - {0}".format(exc_type))
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        LOG.error(''.join('!! ' + line for line in lines))


if __name__ == "__main__":
    global LOG
    logging.config.fileConfig(LOGGING_CONF)
    LOG = logging.getLogger()

    for handler in LOG.handlers:
        if handler.level < logging.ERROR:
            handler.addFilter(puresilliness.util.ErrorFilter())

    LOG.info("Starting mail processor")

    gevent.signal(signal.SIGINT, shutdown)
    gevent.signal(signal.SIGTERM, shutdown)

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(SOCKET_PATH)
    if SOCKET_PATH.startswith('ipc://'):
        # make sure to chmod g+s the directory you are using for the ipc socket
        # so the ipc file will have the proper group
        os.chmod(SOCKET_PATH.replace('ipc://', ''), 0666)

    while True:
        message_string = socket.recv()
        # currently the contents of acknowledgment message are ignored but
        # sending the message is require for the REQ/REP zeromq pattern.
        LOG.debug("Fetched a message")
        socket.send("ack")
        gevent.spawn(process_email, message_string)
