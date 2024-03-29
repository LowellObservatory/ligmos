# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on Wed Feb 21 14:12:11 2018
#
#  @author: rhamilton

from __future__ import division, print_function, absolute_import

import time
import numpy as np

import serviceping
from . import multialarm


def calcMedian(vals):
    """
    """
    # print("Pings:", vals)
    if all(np.isnan(vals)):
        avg = -9999.
    else:
        avg = np.nanmedian(vals)

    return avg


def ping(host, port=22, repeats=7, waittime=0.5, timeout=1,
         median=True, debug=False):
    """
    Want a decent number of pings since some hosts (like OS X) can
    take a few seconds to wake up their hard drives if they're sleeping

    Also want to give them a decent number of seconds to wake up, since
    the timeout doesn't issue an exception but does just give up
    """
    nretries = 0
    dropped = 0
    pres = []
    dnss = []
    while nretries < repeats:
        with multialarm.Timeout(id_="Pings", seconds=timeout):
            try:
                res = serviceping.scan(host, port=port, timeout=timeout)
                # As of serviceping 18.x, res['durations']['connect']
                #   is a datetime.timedelta object! So convert.
                pres.append(res['durations']['connect'].total_seconds()*1000.)
                dnss.append(res['durations']['dns'].total_seconds()*1000.)
                if debug is True:
                    print(res)
            except (TimeoutError, multialarm.TimeoutError) as err:
                # Small quirk; I had thought I needed to call this
                #   multialarm.TimeoutError, but I think because that lib
                #   overloads TimeoutError I just need to catch that one now
                #   sometimes, for reasons unknown.  Namespaces are weird.
                if debug is True:
                    print("Timed out: %s" % (str(err)))
                dropped += 1
                pres.append(np.nan)
                dnss.append(np.nan)
            except serviceping.network.ScanFailed as err:
                pres.append(np.nan)
                dnss.append(np.nan)
                dropped += 1
                if debug is True:
                    print("Connection to host '%s' failed!" % (host))
                    print(str(err))
            nretries += 1
            time.sleep(waittime)

    if median is True:
        ping = calcMedian(pres)
        dns = calcMedian(dnss)
    else:
        ping = pres
        dns = dnss

    if dropped == 7:
        ping = -9999.
        dns = -9999.

    return ping, dropped, dns
