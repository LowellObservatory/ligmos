# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 12 Feb 2020
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

import xmltodict as xmld
from stomp.listener import ConnectionListener

import ligmos.utils as utils


class customConsumer(ConnectionListener):
    def __init__(self):
        """
        ALL listeners need to subclass ConnectionListener.
        The listener will work in it's own thread, and on_message() is called
        for each message on subscribed topics.

        See also:
        https://github.com/LowellObservatory/DataServants/blob/master/dataservants/iago/listener.py
        https://github.com/LowellObservatory/DataServants/blob/master/dataservants/iago/parsetopics.py
        """
        # Grab all the schemas that are in the ligmos library
        self.schemaDict = utils.amq.schemaDicter()

    def on_message(self, headers, body):
        """
        Basically subclassing stomp.listener.ConnectionListener.
        This is called for each and every message from a subscribed topic,
        so don't dilly dally in here!
        """
        # This is used to flag messages that ... well, are bad in some way.
        badMsg = False

        # This is the actual topic name the message came from
        tname = headers['destination'].split('/')[-1].strip()

        # Occasionally, there can be a bit of gibberish due to a network break
        #   or other network gremlin.  So it's best to manually turn the
        #   message bytestring into a regular string.
        try:
            body = body.decode("utf-8")
            badMsg = False
        except UnicodeDecodeError as err:
            print(str(err))
            print("Badness 10000")
            print(body)
            badMsg = True

        if badMsg is False:
            try:
                # Attempt to turn the XML into a dictionary
                #   using the xmltodict package
                xml = xmld.parse(body)
                # We store the dict as an object with the topic name as a key
                #   to make it easier to reference a little later on.  Keep
                #   the headers with us as well since they're handy for
                #   debugging later failures.
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
                print(str(err))
                print("="*42)
                badMsg = True

        # Now send the packet to the right place for processing.
        if badMsg is False:
            # Wrap everything in a try...except because it'll help catch
            #   and actually handle errors, rather than just crashing out
            try:
                if tname.lower() == "topicNeedingSpecialHandling":
                    # Call your custom parser here
                    pass
                elif tname in self.schemaDict.keys():
                    schema = self.schemaDict[tname]
                    print("Potential schema found:")
                    print(schema)
                    # Call your schema-enabled parser here
                else:
                    # Warn about stuff not handled
                    print("Orphan topic: %s" % (tname))
                    print(headers)
                    print(body)
                    print(res)
            except Exception as err:
                # Mostly this catches instances where the topic name doesn't
                #   have a valid schema, but it catches all oopsies really.
                # Very helpful for debugging.
                print("="*11)
                print(str(err))
                print(headers)
                print(body)
                print("="*11)
