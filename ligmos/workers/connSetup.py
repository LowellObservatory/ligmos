# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 24 Jun 2019
#
#  @author: rhamilton

"""
"""

from __future__ import division, print_function, absolute_import

from ..utils import amq
from ..utils import database


def connAMQ(comm, amqtopics, amqlistener=None):
    """
    Set up the actual connections, which we'll then give back to the actual
    objects for them to do stuff with afterwards.
    """
    amqbrokers = {}

    for commsection in comm:
        # Rename for easier access/passing
        cobj = comm[commsection]

        # Now check the properties of this object to see if it's something we
        #   actually regconize and then connect to
        if cobj.type.lower().startswith('activemq'):
            # We get brokerlistener back as a return just in case it was
            #   None initially, in which case amq.setupBroker would give one
            conn, amqlistener = amq.setupAMQBroker(cobj,
                                                   amqtopics[commsection],
                                                   listener=amqlistener)

            # Store this so we can check/use it later
            brokerbits = [conn, amqlistener]
            amqbrokers.update({commsection: brokerbits})
        else:
            # No other types are defined yet
            pass

    return amqbrokers


def connIDB(comm):
    """
    Set up the actual connections, which we'll then give back to the actual
    objects for them to do stuff with afterwards.
    """
    influxdatabases = {}

    for commsection in comm:
        # Rename for easier access/passing
        cobj = comm[commsection]

        # Now check the properties of this object to see if it's something we
        #   actually regconize and then connect to
        if cobj.type.lower() == 'influxdb':
            # Create an influxdb object that can be spread around to
            #   connect and commit packets when they're created.
            #   Leave it disconnected initially.
            # Check to see if we've stuffed in a table name to use
            if hasattr(cobj, 'tablename') is True:
                tbl = cobj.tablename
            else:
                tbl = None

            idb = database.influxobj(host=cobj.host,
                                     port=cobj.port,
                                     user=cobj.user,
                                     tablename=tbl,
                                     pw=cobj.password,
                                     connect=False)

            # Connect briefly to check/verify everything is working
            idb.connect()
            idb.disconnect()

            # Store this so we can check/use it later
            influxdatabases.update({commsection: idb})
        else:
            # No other types are defined yet
            pass

    return influxdatabases
