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

import stomp
import xmlschema as xmls
import pkg_resources as pkgr


class amqHelper():
    def __init__(self, default_host, topics=None,
                 dbname=None, user=None, passw=None, port=61613,
                 baseid=8675309, connect=True, listener=None):
        self.host = default_host
        self.port = port
        self.topics = topics
        self.baseid = baseid
        self.dbname = dbname
        self.user = user
        self.password = passw

        if connect is True:
            self.connect(listener=listener)
            if topics is not None:
                self.subscribe(self.topics, baseid=baseid)
        else:
            self.conn = None

    def connect(self, listener=None):
        # TODO:
        #   Put a timer on connection
        try:
            print("Connecting to %s" % (self.host))
            self.conn = stomp.Connection([(self.host, self.port)],
                                         auto_decode=False)
            # Note that self.conn is now type stomp.connect.StompConnectionXX
            #   where XX is either 10, 11, or 12 indicating STOMP version
            if listener is not None:
                # NOTE: listener must be a valid ConnectionListener type!!
                self.conn.set_listener('LIGmosSpy', listener)

            # For STOMP.py versions >= 4.1.20, .start() does nothing.
            self.conn.start()
            self.conn.connect()
            print("Connection established. Hooray!")

            if self.topics is not None:
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
        if self.conn is not None:
            self.conn.disconnect()
            print("Disconnected from %s" % (self.host))

    def subscribe(self, topic, baseid=8675309):
        if self.conn is not None:
            if type(self.topics) == str:
                    self.conn.subscribe("/topic/" + self.topics, baseid)
            elif type(self.topics) == list:
                for i, activeTopic in enumerate(self.topics):
                    print("Subscribing to %s" % (activeTopic))
                    self.conn.subscribe("/topic/" + activeTopic, baseid+i)

    def publish(self, dest, message, mtype='text', debug=True):
        """
        TODO:
        What are the accepted values for 'amq-msg-type' and
        do we need to worry at all about them?
        No clue currently.
        """

        # Note: If it doesn't start with /topic/ it'll fail silently!
        if not dest.startswith('/topic/'):
            topic = '/topic/' + dest
        else:
            topic = dest

        if self.conn is not None:
            self.conn.send(destination=topic, body=message,
                           headers={'amq-msg-type': 'text'})
        info = "\nMessage sent to {} on topic {}:\n{}\n"
        if debug is True:
            print(info.format(self.host, topic, message))


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
