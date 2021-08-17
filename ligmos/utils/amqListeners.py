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

import urllib

import xmltodict as xmld
from stomp.listener import ConnectionListener

from . import amq
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
    def __init__(self, dbconn=None, postProcFunc=None, tSpecial=None,
                 tXML=None, tFloat=None, tStr=None, tBool=None):
        """
        This will really be stuffed into a
        amqHelper class, so all the connections stuff is
        really over there in that class.  This is just to route
        specific messages to the right parsers
        """
        # This should be a function reference that will be used first
        #   if specified, to handle any special cases that aren't handled
        #   by one of the generic parsers below
        self.postProcFunc = postProcFunc
        self.tSpecial = tSpecial

        # These topics are handeled entirely by generic parsers
        self.tXML = tXML
        self.tFloat = tFloat
        self.tStr = tStr
        self.tBool = tBool

        # Database handle
        self.dbconn = dbconn

        if self.tXML is not None:
            # This ONLY makes sense if there are XML topics
            #   Grab all the schemas that are in the ligmos library
            self.schemaDict = myxml.schemaDicter()
            self.schemaList = list(self.schemaDict.keys())
            print(self.schemaDict)
        else:
            self.schemaDict = None
            self.schemaList = None

    def on_message(self, headers, body):
        """
        """
        badMsg = False
        tname = headers['destination'].split('/')[-1].strip()

        # Manually turn the bytestring into a string
        try:
            body = body.decode("utf-8")
            badMsg = False
        except UnicodeDecodeError as err:
            print(str(err))
            print("Badness 10000")
            print(body)
            badMsg = True

        # Now send the packet to the right place for processing.
        if badMsg is False:
            try:
                if tname in self.tXML:
                    schema = myxml.findNamedSchema(self.schemaList,
                                                   self.schemaDict,
                                                   tname)

                    mp.parserFlatPacket(headers, body,
                                        schema=schema, db=self.dbconn,
                                        returnParsed=False)
                elif (self.tFloat is not None) or (self.tFloat is not None) or\
                     (self.tBool is not None) or (self.tStr is not None):
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
                    # Intended to be the endpoint of the auto-XML publisher
                    #   so I can catch most of them rather than explicitly
                    #   check in the if/elif block above
                    print("Orphan topic: %s" % (tname))
                    print(headers)
                    print(body)
            except urllib.error.URLError as err:
                # This actually implies that the message wasn't a valid XML
                #   message and couldn't actually be validated.  I think it's
                #   really a quirk of the xmlschema library but I'm not sure
                print(err)
            except Exception as err:
                # Mostly this catches instances where the topic name doesn't
                #   have a schema, but it catches all oopsies really
                print("="*11)
                print("WTF!!!")
                print(str(err))
                print(headers)
                print(body)
                print("="*11)
