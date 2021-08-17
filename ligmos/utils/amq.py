# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 21 May 2018
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

import secrets

import stomp

from . import classes
from . import amqListeners as amql


class amqHelper():
    def __init__(self, default_host, topics=None, user=None, passw=None,
                 port=61613, baseid='ligmos', connect=True, listener=None,
                 protocol=None):
        self.host = default_host
        self.port = port
        self.topics = topics
        self.baseid = baseid
        self.user = user
        self.password = passw
        self.protocol = protocol

        # Setting up a default endpoint so we at least always see the
        #   messages on the subscribed topics. If you want a silent
        #   experience, then make one or directly pass in the default
        #   stomp.listener ConnectionListener
        if listener is None:
            listener = amql.ParrotSubscriber()

        if connect is True:
            self.connect(listener=listener)
            if topics is not None:
                # This is the class subscribe method, not the STOMP one
                # NOTE: By leaving topic=None here (the default) the method
                #   just picked up topics from self.topics instead.  That's
                #   confusing but it's vestigial and not super important.
                self.subscribe()
        else:
            self.conn = None

    def connect(self, listener=None, subscribe=True):
        """
        """
        # TODO:
        #   Put a timer on connection

        try:
            print("Connecting to %s" % (self.host))
            if self.protocol is None:
                self.protocol = 'stompLatest'

            if self.protocol.lower() == 'stomp10':
                self.conn = stomp.Connection10([(self.host, self.port)],
                                               auto_decode=False)
            elif self.protocol.lower() == 'stomp11':
                self.conn = stomp.Connection11([(self.host, self.port)],
                                               auto_decode=False,
                                               heartbeats=(10000, 10000),
                                               heart_beat_receive_scale=3.0)
            else:
                self.conn = stomp.Connection([(self.host, self.port)],
                                             auto_decode=False,
                                             heartbeats=(10000, 10000),
                                             heart_beat_receive_scale=3.0)

            # Note that self.conn is now type stomp.connect.StompConnectionXX
            #   where XX is either 10, 11, or 12 indicating STOMP version
            if listener is not None:
                # NOTE: listener must be a valid ConnectionListener type!!
                self.conn.set_listener('LIGmosSpy', listener)
            else:
                print("WARNING! No listener defined! Nothing will occur!")

            # For STOMP.py versions >= 4.1.20, .start() does nothing and
            #   actually won't even exist so it'll throw AttributeError.
            #   That's totally cool so just ignore it.
            # Old brokers might fall back to StompConnection10, which requires
            #   the start() method to actually be used before connect().
            #   The ancient broker for Solaris running for NASA42 is an
            #   example of this so I need this here still.
            try:
                self.conn.start()
            except AttributeError:
                pass

            self.conn.connect()
            print("Connection established. Hooray!")

            if subscribe is True:
                if self.topics is not None:
                    print("Subscribing to:")
                    print(self.topics)
                    self.subscribe(topic=self.topics)
        except stomp.exception.NotConnectedException as err:
            self.conn = None
            print("STOMP.py not connected!")
        except stomp.exception.ConnectFailedException as err:
            self.conn = None
            print("STOMP.py connection failed!")
        except stomp.exception.StompException as err:
            self.conn = None
            print("STOMP.py exception!")
            print(str(type(err)))

    def disconnect(self):
        """
        """
        if self.conn is not None:
            self.conn.disconnect()
            print("Disconnected from %s" % (self.host))

    def subscribe(self, topic=None):
        """
        NOTE: This is the method of the amqHelper class!  Not the STOMP one!

        If given a topic argument, subscribe to just that one.
        If it's not given, check for anything to subscribe to in
        the self.topics property.  It's one, or the other. NOT BOTH.
        """
        if topic is not None:
            sub = topic
        else:
            sub = self.topics

        if self.conn is not None:
            if isinstance(sub, str):
                tid = "%s_%s" % (self.baseid, secrets.token_hex(nbytes=8))
                tstr = "/topic/" + sub
                # NOTE this is the STOMP.py subscribe call here.  stomp10
                #   still lingers, and id is a keyword param so do it
                if self.protocol == 'stomp10':
                    self.conn.subscribe(tstr, id=tid)
                else:
                    self.conn.subscribe(tstr, tid)
            elif isinstance(sub, list):
                for activeTopic in sub:
                    print("Subscribing to %s" % (activeTopic))
                    tid = "%s_%s" % (self.baseid, secrets.token_hex(nbytes=8))
                    tstr = "/topic/" + activeTopic
                    if self.protocol == 'stomp10':
                        self.conn.subscribe(tstr, id=tid)
                    else:
                        self.conn.subscribe(tstr, tid)

    def publish(self, dest, message, mtype='text', replyto=None, debug=True):
        """
        TODO:
        What are the accepted values for 'amq-msg-type' and
        do we need to worry at all about them?
        No clue currently.
        """

        topic = checkTopic(dest)

        if self.conn is not None:
            if replyto is None:
                self.conn.send(destination=topic, body=message,
                               headers={'amq-msg-type': mtype})
            else:
                replyto = checkTopic(replyto)
                self.conn.send(destination=topic, body=message,
                               headers={'amq-msg-type': mtype,
                                        'reply-to': replyto})
        info = "\nMessage sent to {} on topic {}:\n{}\n"
        if debug is True:
            print(info.format(self.host, topic, message))


def setupAMQBroker(cblk, topics, baseid='ligmos', listener=None):
    """
    """
    # ActiveMQ connection checker
    conn = None

    # Register the listener class for this connection.
    #   This will be the thing that parses packets depending
    #   on their topic name and does the hard stuff!
    # If you don't specify one, the default (print-only) one will be used.
    if listener is None:
        listener = amql.ParrotSubscriber()

    # Check to see if we have any specific ActiveMQ version hints
    #   NOTE: I forgot I did this, but it's handled better by the
    #         'protocol' config option added to the baseTarget class
    btype = cblk.type
    if cblk.protocol is None:
        # Check for this old hint
        bver = btype.strip().split("_")
        if len(bver) > 1:
            try:
                bver = int(bver[-1])
                if bver == 10:
                    bver = 'stomp10'
                elif bver == 11:
                    bver = 'stomp11'
                else:
                    print("Unknown version! %d" % (bver))
                    bver = None
            except ValueError:
                print("Unknown ActiveMQ/STOMP version hint!")
                print("%s" % (btype))
        else:
            bver = None
    else:
        # Assume whatever was in the common block was what we wanted
        #   This should all be cleaned up, someday...
        bver = cblk.protocol

    # Establish connections and subscriptions w/our helper
    # TODO: Figure out how to fold in broker passwords
    print("Connecting to %s" % (cblk.host))
    conn = amqHelper(cblk.host,
                     topics=topics,
                     user=cblk.user,
                     passw=cblk.password,
                     port=cblk.port,
                     baseid=baseid,
                     connect=False,
                     listener=listener,
                     protocol=bver)

    return conn, listener


def checkSingleConnection(broker, subscribe=True):
    """
    This is intended to be inside of some loop structure.
    It's primarily used for checking whether the connection to the ActiveMQ
    broker is still valid, and, if it was killed (set to None) because the
    heartbeat failed, attempt to both reconnect and resubscribe to the
    topics.
    """
    connChecking = broker[0]
    thisListener = broker[1]

    if connChecking.conn is None:
        print("No connection at all! Retrying...")
        # The topics were already stuffed into the connChecking object,
        #   but it's nice to remember that we're subscribing to them
        connChecking.connect(listener=thisListener, subscribe=subscribe)
    elif connChecking.conn.transport.connected is False:
        print("Connection died! Reestablishing...")
        connChecking.connect(listener=thisListener, subscribe=subscribe)
    else:
        print("Connection still valid")

    # Make sure we save any connection changes and give it back
    broker = [connChecking, thisListener]

    return broker


def checkConnections(amqbrokers, quiet=True, subscribe=True):
    """
    This is intended to be inside of some loop structure.
    It's primarily used for checking whether the connection to the ActiveMQ
    broker is still valid, and, if it was killed (set to None) because the
    heartbeat failed, attempt to both reconnect and resubscribe to the
    topics.
    """
    for bconn in amqbrokers:
        # From above, amqbrokers is a dict with values that are a list of
        #   connection object, list of topics, listener object
        connChecking = amqbrokers[bconn][0]
        thisListener = amqbrokers[bconn][1]
        if connChecking.conn is None:
            print("No connection at all! Retrying...")
            # The topics were already stuffed into the connChecking object,
            #   but it's nice to remember that we're subscribing to them
            connChecking.connect(listener=thisListener, subscribe=subscribe)
        elif connChecking.conn.transport.connected is False:
            print("Connection died! Reestablishing...")
            connChecking.connect(listener=thisListener, subscribe=subscribe)
        else:
            if quiet is False:
                print("Connection still valid")

        # Make sure we save any connection changes and give it back
        amqbrokers[bconn] = [connChecking, thisListener]

    return amqbrokers


def gatherTopics(iobj, queuerole=None):
    """
    The actual workhorse function that checks the actual topics, which
    can be in different attributes depending on the exact type of object
    that we're dealing with (e.g. brokerCommandingTarget vs. snoopTarget)
    """
    topics = []
    if isinstance(iobj, classes.brokerCommandingTarget):
        # This is optional so check first. We don't actually need
        #   iobj.cmdtopic since it's a producer topic, and is where the
        #   commands will be coming in from.
        if queuerole is None:
            print("ERROR! Must supply a queue role (server or cilent)")
        else:
            if queuerole.lower() == 'client':
                if iobj.replytopic is not None:
                    topics.append(iobj.replytopic)
            elif queuerole.lower() == 'server':
                if iobj.cmdtopic is not None:
                    topics.append(iobj.cmdtopic)

    elif isinstance(iobj, classes.instrumentDeviceTarget):
        # This is optional so check first.
        if iobj.devbrokerreply is not None:
            topics.append(iobj.devbrokerreply)
    elif isinstance(iobj, classes.sneakyTarget):
        topics.append(iobj.pubtopic)
    elif isinstance(iobj, classes.snoopTarget):
        eachesTopics = iobj.topics
        # Attempt to deal with single vs. multi-topic possibilities
        if isinstance(eachesTopics, list):
            topics += eachesTopics
        elif isinstance(eachesTopics, str):
            topics.append(eachesTopics)

    # A final downselect to make sure we don't have any duplicates
    topics = list(set(topics))

    return topics


def getAllTopics(config, comm, queuerole=None):
    """
    Given a parsed configuration and common set of stuff, search thru
    the former looking for any/all ActiveMQ broker topics and return them
    to the caller, organized by broker tag. This makes our
    connection/reconnection/subscription logic waaaaayy easier
    """
    amqtopics = {}
    for sect in config:
        csObj = config[sect]
        try:
            brokerTag = csObj.broker
            brokertype = comm[brokerTag].type
        except AttributeError:
            # If we end up in here, that means that it wasn't actually
            #   a broker section so just skip it
            brokerTag = ''
            brokertype = ''

        if brokertype.lower().startswith('activemq'):
            # Gather up broker stuff
            try:
                # First see if we have anything previously gathered, to make
                #   sure we don't accidentally clobber anything
                alltopics = amqtopics[brokerTag]
            except KeyError:
                alltopics = []

            # Get the topics; it's guaranteed to be a list
            thesetopics = gatherTopics(csObj, queuerole=queuerole)
            alltopics += thesetopics

            # list(set()) to quickly take care of any dupes
            amqtopics.update({brokerTag: list(set(alltopics))})

    # Now we need to check for any queue topics, and grab those
    for sect in comm:
        csObj = comm[sect]
        try:
            brokerTag = csObj.broker
            commtype = csObj.type
        except AttributeError:
            # If we end up in here, it wasn't a broker section so skip it
            brokerTag = ''
            commtype = ''

        if commtype.lower() == 'queue':
            thesetopics = gatherTopics(csObj, queuerole=queuerole)
            alltopics += thesetopics

            # list(set()) to quickly take care of any dupes
            amqtopics.update({brokerTag: list(set(alltopics))})

    return amqtopics


def checkTopic(tpc):
    """
    If the ActiveMQ topic string doesn't start with /topic/ it'll fail!
        This adds it if it's not already there.
    """
    if not tpc.lower().startswith('/topic/') or \
       not tpc.lower().startswith('/queue/'):
        # If it's not already a topic or a queue, assume that it's at least
        #   a topic so it won't get silently ignored. Not the best, but
        #   not bad of a start at least.
        topic = '/topic/' + tpc
    else:
        # Otherwise assume that it's ok as-is
        topic = tpc

    return topic


def disconnectAll(amqbrokers):
    """
    A helpful cleanup routine
    """
    for bconn in amqbrokers:
        # From above, amqbrokers is a dict with values that are a list of
        #   connection object, list of topics, listener object
        connChecking = amqbrokers[bconn][0]
        connChecking.disconnect()
