# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 12 Feb 2020
#
#  @author: rhamilton

"""brokerConnection

Simple example to show how to connecto to an ActiveMQ broker with stomp.py,
and use the heartbeat to tell if your connection is broken or not.
"""

from __future__ import division, print_function, absolute_import

import time

from ligmos import utils


if __name__ == "__main__":
    default_host = 'joe.lowell.edu'
    bigsleep = 30

    topics = ['AOS.AOSSubDataSV.AbsoluteFocusOffset',
              'AOS.AOSSubDataSV.RelativeFocusOffset',
              'AOS.AOSSubDataSV.ClearFocusOffset',
              'lmi.loisTelemetry',
              'TCS.TCSSharedVariables.TCSHighLevelStatusSV.TCSTcsStatusSV']

    print("Setting up listener...")
    listener = utils.amq.ParrotSubscriber(dictify=False)

    conn = utils.amq.amqHelper(default_host,
                               topics,
                               user=None,
                               passw=None,
                               port=61613,
                               connect=False,
                               listener=listener)

    # This helper class catches various signals; see
    #   ligmos.utils.common.HowtoStopNicely() for details
    runner = utils.common.HowtoStopNicely()

    # All LIG codes are run in docker containers so infinite loops are the norm
    while runner.halt is False:
        # Double check that the connection is still up
        #   NOTE: conn.connect() handles ConnectionError exceptions
        if conn.conn is None:
            print("No connection!  Attempting to connect ...")
            conn.connect(listener=listener)
        elif conn.conn.transport.connected is False:
            # Added the "first" flag to take care of a double sub. bug
            print("Connection died! Reestablishing ...")
            conn.connect(listener=listener)
        else:
            print("Connection still valid")

        # Consider taking a big nap
        if runner.halt is False:
            print("Starting a big sleep")
            # Sleep for bigsleep, but in small chunks to check abort
            for _ in range(bigsleep):
                time.sleep(0.5)
                if runner.halt is True:
                    break

    # Disconnect from the ActiveMQ broker
    conn.disconnect()
