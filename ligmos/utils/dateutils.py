# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 7 Jun 2019
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

import datetime as dt
from os.path import basename


def dateDiff(fstr, debug=False):
    """Attempt to determine how old a given string is from now.

    Depends entirely on :func:`strToDate` to convert the given
    string ``fstr`` into a datetime object.  Assumes that ``fstr`` is really
    a directory path, so it first takes the :func:`os.path.basename` of it.

    Args:
        fstr (:obj:`str`)
            Full path of a folder to be dated
        debug (:obj:`bool`, optional)
            Bool to trigger additional debugging outputs. Defaults to False.

    Returns:
        diff (:class:`datetime.timedelta`)
            Timedelta instance between now and the parsed
            and converted ``fstr``. If ``fstr`` couldn't be converted,
            diff will be :obj:`None`.
    """
    dstr = basename(fstr)
    dtobj = strToDate(dstr)
    if type(dtobj) is dt.datetime:
        dtts = dt.datetime.timestamp(dtobj)
        now = dt.datetime.timestamp(dt.datetime.utcnow())
        diff = (now - dtts)

        if debug is True:
            print(dstr, dtobj, dtts, now, diff)
    else:
        # Obvious bad value so others can deal with it in their logic
        diff = None

    return diff


def strToDate(st):
    """Attempt to convert the given string to a datetime.

    First assumes that just the first 8 characters are good enough,
    which would match strings like "20180415...".

    If that doesn't work, it tries to match strings like "2018-04-15".

    If that doesn't work, it gives up.  Could obviously be extended further.

    Args:
        st (:obj:`str`)
            String to attempt to convert

    Returns:
        dted (:class:`datetime.datetime`)
            Datetime instance converted from string, using
            :func:`datetime.strptime`.

            .. note::
                :func:`datetime.strptime` is hard to link to, so look at
                :func:`time.strptime`, and the stuff defined in
                :func:`time.strftime`.  See also the helpful table at
                `strftime() and strptime() Behavior
                <https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior>`_.

    """
    # Try just the first 8 characters (20180214, 20180214a, 20180214_junk)
    dted = None
    try:
        dted = dt.datetime.strptime(st[0:8], "%Y%m%d")
    except ValueError:
        # Try some other ones
        if len(st) == 10:
            try:
                dted = dt.datetime.strptime(st, "%Y-%m-%d")
            except ValueError:
                # dted will still be None at this point,
                #   so now it becomes the calling function's problem
                pass

    return dted
