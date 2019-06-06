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

from os.path import basename

import stomp
import xmltodict as xmld
import xmlschema as xmls
import pkg_resources as pkgr


class silentSubscriber(stomp.listener.ConnectionListener):
    def __init__(self):
        pass


class commandSubscriber(stomp.listener.ConnectionListener):
    def __init__(self):
        pass

        # Subclassing stomp.listener.ConnectionListener
    def on_message(self, headers, body):
        tname = headers['destination'].split('/')[-1]
        # Manually turn the bytestring into a string
        try:
            body = body.decode("utf-8")
            badMsg = False
        except Exception as err:
            print(str(err))
            print("Badness 10000")
            print(body)
            badMsg = True

        if badMsg is False:
            try:
                xml = xmld.parse(body)
                # If we want to have the XML as a string:
                # res = {tname: [headers, dumpPacket(xml)]}
                # If we want to have the XML as an object:
                res = {tname: [headers, xml]}
            except Exception as err:
                # This means that there was some kind of transport error
                #   or it couldn't figure out the encoding for some reason.
                #   Scream into the log but keep moving
                print("="*42)
                print(headers)
                print(body)
                print("="*42)
                badMsg = True

        print("Message Source: %s" % (tname))
        if badMsg:
            print("Header: %s" % (headers))
            print("Body: %s" % (body))
        else:
            print(tname, xml)


class ParrotSubscriber(stomp.listener.ConnectionListener):
    """
    Default subscriber that will at least print out stuff
    """
    def __init__(self):
        pass

    # Subclassing stomp.listener.ConnectionListener
    def on_message(self, headers, body):
        tname = headers['destination'].split('/')[-1]
        # Manually turn the bytestring into a string
        try:
            body = body.decode("utf-8")
            badMsg = False
        except Exception as err:
            print(str(err))
            print("Badness 10000")
            print(body)
            badMsg = True

        if badMsg is False:
            try:
                xml = xmld.parse(body)
                # If we want to have the XML as a string:
                # res = {tname: [headers, dumpPacket(xml)]}
                # If we want to have the XML as an object:
                res = {tname: [headers, xml]}
            except xmld.expat.ExpatError:
                # This means that XML wasn't found, so it's just a string
                #   packet with little/no structure. Attach the sub name
                #   as a tag so someone else can deal with the thing
                res = {tname: [headers, body]}
            except Exception as err:
                # This means that there was some kind of transport error
                #   or it couldn't figure out the encoding for some reason.
                #   Scream into the log but keep moving
                print("="*42)
                print(headers)
                print(body)
                print("="*42)
                badMsg = True

        print("Message Source: %s" % (tname))
        if badMsg:
            print("Header: %s" % (headers))
            print("Body: %s" % (body))
        else:
            print(res)


class amqHelper():
    def __init__(self, default_host, topics=None,
                 user=None, passw=None, port=61613,
                 baseid=8675309, connect=True, listener=None):
        self.host = default_host
        self.port = port
        self.topics = topics
        self.baseid = baseid
        self.user = user
        self.password = passw

        # Setting up a default endpoint so we at least always see the
        #   messages on the subscribed topics. If you want a silent
        #   experience, then make one or directly pass in the default
        #   stomp.listener ConnectionListener
        if listener is None:
            listener = ParrotSubscriber()

        if connect is True:
            self.connect(listener=listener)
            if topics is not None:
                self.subscribe(self.topics, baseid=baseid)
        else:
            self.conn = None

    def connect(self, listener=None, subscribe=True):
        """
        """
        # TODO:
        #   Put a timer on connection

        # Do I really need to duplicate this check that I do in __init__ ?
        #   Seems like I just need to choose one or the other, but I'm leaving
        #   this here since I think I have some codes that need this check.
        if listener is None:
            listener = ParrotSubscriber()

        try:
            print("Connecting to %s" % (self.host))
            self.conn = stomp.Connection([(self.host, self.port)],
                                         auto_decode=False,
                                         heartbeats=(4000, 4000),
                                         heart_beat_receive_scale=2.0)
            # Note that self.conn is now type stomp.connect.StompConnectionXX
            #   where XX is either 10, 11, or 12 indicating STOMP version
            if listener is not None:
                # NOTE: listener must be a valid ConnectionListener type!!
                self.conn.set_listener('LIGmosSpy', listener)
            else:
                print("WARNING! No listener defined! Nothing will occur!")

            # For STOMP.py versions >= 4.1.20, .start() does nothing.
            self.conn.start()
            self.conn.connect()
            print("Connection established. Hooray!")

            if subscribe is True:
                if self.topics is not None:
                    print("Subscribing to:")
                    print(self.topics)
                    self.subscribe(self.topics)
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

    def subscribe(self, topic, baseid=8675309):
        """
        """
        if self.conn is not None:
            if type(self.topics) == str:
                self.conn.subscribe("/topic/" + self.topics, baseid)
            elif type(self.topics) == list:
                for i, activeTopic in enumerate(self.topics):
                    print("Subscribing to %s" % (activeTopic))
                    self.conn.subscribe("/topic/" + activeTopic, baseid+i)

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
                               headers={'amq-msg-type': 'text'})
            else:
                replyto = checkTopic(replyto)
                self.conn.send(destination=topic, body=message,
                               headers={'amq-msg-type': 'text',
                                        'reply-to': replyto})
        info = "\nMessage sent to {} on topic {}:\n{}\n"
        if debug is True:
            print(info.format(self.host, topic, message))


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


def checkSchema(topicname):
    """
    """
    # Put together the expected schema name
    sn = 'schemas/' + topicname + '.xsd'
    try:
        # Define the schema we'll use to convert datatypes. If it doesn't
        #   exist, catch the exception and return 'None' to show that
        #   the schema didn't exist where it was expected
        sf = pkgr.resource_filename('ligmos', sn)
        schema = xmls.XMLSchema(sf)
        return schema
    except xmls.XMLSchemaURLError:
        print("Schema for topic %s not found!" % (topicname))
        return None


def schemaDicter():
    """
    Grab all of the schemas in the package directory and return
    a dict organized by topic name.
    """
    sdict = {}

    # Get the list of everything in the schema repo
    allschemas = pkgr.resource_listdir('ligmos', 'schemas')

    for tsch in allschemas:
        spath = "%s/%s" % ('schemas', tsch)
        schname = basename(tsch)

        # Strip the file extension off of it!
        schname = schname[:-4]

        if pkgr.resource_isdir('ligmos', spath):
            print("%s is a directory! Skipping it." % (tsch))
        else:
            print("%s is a potential schema! Looking at it." % (schname))

            try:
                # Define the schema we'll use to convert datatypes
                sf = pkgr.resource_filename('ligmos', spath)
                schema = xmls.XMLSchema(sf)
                sdict.update({schname: schema})
            except xmls.XMLSchemaURLError:
                print("Schema for topic %s not found!" % (schname))

    return sdict
