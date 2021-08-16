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
from os.path import basename

import stomp
import xmltodict as xmld
import xmlschema as xmls
import pkg_resources as pkgr

from . import classes


class silentSubscriber(stomp.listener.ConnectionListener):
    """
    Silent, but deadly (if you don't realize it is fully silent)
    """
    def __init__(self):
        pass


class ParrotSubscriber(stomp.listener.ConnectionListener):
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
