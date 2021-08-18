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

import xmltodict as xmld
from stomp.listener import ConnectionListener

from . import xmlschemas as myxml
from . import messageParsers as mp


class silentSubscriber(ConnectionListener):
    """
    Silent, but deadly (if you don't realize it is fully silent)

    Used primarily when you need to publish but not really listen.
    """
    def __init__(self):
        pass


class ParrotSubscriber(ConnectionListener):
    """
    Default subscriber that will at least print out stuff
    """
    def __init__(self, dictify=True, baseid='ligmos'):
        self.dictify = dictify
        self.baseid = baseid

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
                if self.dictify is True:
                    xml = xmld.parse(body)
                    res = {tname: [headers, xml]}
                else:
                    # If we want to have the XML as a string:
                    res = {tname: [headers, body]}

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
            if self.dictify is True:
                print(res)
            else:
                print(headers['timestamp'], body)


class LIGBaseConsumer(ConnectionListener):
    """
    This will really be stuffed into an amqHelper class, so all the
    connections stuff is really over there in that class.
    """
    def __init__(self, dbconn=None,
                 tXML=None, tFloat=None, tStr=None, tBool=None,
                 tSpecial=None):

        # This should be a *dict* mapping the topic name to a bound method
        #   that is the special/specific parser for that topic.  That lets us
        #   handle any any special cases that aren't generic
        if isinstance(tSpecial, dict):
            self.specialMap = tSpecial
            self.specialTopics = list(tSpecial.keys())
        else:
            print("WARNING: No special topics, or improper format!")
            self.specialMap = None
            self.specialTopics = []

        # These topics are handeled entirely by generic parsers
        self.tXML = tXML
        self.tFloat = tFloat
        self.tStr = tStr
        self.tBool = tBool

        # Database handle
        self.dbconn = dbconn

        if self.tXML is None:
            # If we have no XML packets, skip the schema business because
            #   it's really not needed at all for this listener
            self.schemaDict = None
            self.schemaList = None
        else:
            # Grab all the schemas that are in the ligmos library
            self.schemaDict = myxml.schemaDicter()
            self.schemaList = list(self.schemaDict.keys())
            print(self.schemaDict)

    def on_message(self, headers, body):
        """
        """
        badMsg = False
        tname = headers['destination'].split('/')[-1].strip()

        # Manually turn the bytestring into a string
        try:
            body = body.decode("utf-8")
            badMsg = False
            print("Processing message on %s: %s" % (tname, body))
        except UnicodeDecodeError as err:
            print(str(err))
            print("Badness 10000")
            print(body)
            badMsg = True

        # Now send the packet to the right place for processing.
        if badMsg is False:
            try:
                if tname in self.specialTopics:
                    # Look for special topics first!
                    funcRef = self.specialMap[tname]
                    funcRef(headers, body, db=self.dbconn)
                elif tname in self.tXML:
                    # XML (schema-based) second
                    schema = myxml.findNamedSchema(self.schemaList,
                                                   self.schemaDict,
                                                   tname)
                    # A note about time (timestampKey):
                    #   It should be given in sec/ms/nanosec from the epoch,
                    #   already localized to the timezone of your influxdb
                    #   instance.  For many of my things, I've done that in
                    #   the device parsing/preparation state and stored it in
                    #   the XML as "influx_ts_" + ("s" ||  "ms" || "ns")
                    #   depending on the precision available from each device.
                    # If the packet has no key called influx_ts,
                    #   the timestamp will not be parsed and influx itself will
                    #   timestamp the data upon injestion.
                    mp.parserFlatPacket(headers, body,
                                        timestampKey='influx_ts',
                                        schema=schema, db=self.dbconn,
                                        returnParsed=False)
                elif (self.tFloat is not None) or (self.tFloat is not None) or\
                     (self.tBool is not None) or (self.tStr is not None):
                    # Everyting else goes last
                    if tname in self.tFloat:
                        simpleDtype = 'float'
                    elif tname in self.tStr:
                        simpleDtype = 'string'
                    elif tname in self.tBool:
                        simpleDtype = 'bool'
                    else:
                        print("WARNING - Unknown type! Skipping %s" % (tname))
                        simpleDtype = None

                    if simpleDtype is not None:
                        mp.parserSimple(headers, body, db=self.dbconn,
                                        datatype=simpleDtype)
                else:
                    print("Orphan topic: %s" % (tname))
                    print(headers)
                    print(body)
            except Exception as err:
                # Mostly this catches instances where the topic name doesn't
                #   have a schema, but it catches all oopsies really
                print("="*11)
                print("WTF!!!")
                print(str(err))
                print(headers)
                print(body)
                print("="*11)
