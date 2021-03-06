# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on Mon Feb 26 13:16:35 2018
#
#  @author: rhamilton

from __future__ import division, print_function, absolute_import

import sys
import datetime as dt


def makeInfluxPacket(meas='', ts=dt.datetime.utcnow(), tags=None,
                     fields=None, debug=False):
    """
    Makes an InfluxDB styled packet given the measurement name, metadata tags,
    and actual fields/values to put into the database
    """
    packet = {}
    if tags is None:
        tags = {}
    if fields is None:
        fields = {}

    for m in meas:
        packet.update({'measurement': m})
        if tags is not None:
            if not isinstance(tags, dict):
                print("ERROR! tags must be of type dict.")
                sys.exit(-1)
            else:
                packet.update({'tags': tags})

        if isinstance(ts, dt.datetime):
            # InfluxDB wants timestamps in nanoseconds from Epoch (1970/01/01)
            #   but Grafana defaults to ms precision from Epoch.
            #   influxdb-python is a little fuzzy here, so convert it ourselves
            #   (dt.datetime.utcnow() doesn't supply .tzinfo, I think, and
            #     that is what influxdb-python looks for to autoconvert)
            # nsts = int(ts.timestamp() * 1e3)
            pass
        elif isinstance(ts, float):
            print("ERROR! Timestamp can not be a float because dumb.")
            sys.exit(-1)
        elif ts is None:
            # If we don't specify a timestamp, don't even put it in the packet
            pass
        else:
            # Also assume that it's right. But this is probably the
            #   weakest link of all of these
            packet.update({'time': ts})

        if not isinstance(fields, dict):
            print("ERROR! fields must be of type dict.")
            sys.exit(-1)

        packet.update({'fields': fields})

    if debug is True:
        print(packet)

    return [packet]
