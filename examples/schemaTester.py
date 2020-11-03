# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 2 Nov 2020
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

import xmltodict as xmld
import pkg_resources as pkgr

from ligmos import utils


def function1():
    """
    """
    pass


if __name__ == "__main__":
    name = "igrid_liveStatsXML"

    schema = utils.amq.checkSchema(name)
    sample = utils.amq.checkSample(name)

    if sample != "":
        print("Sample XML for %s:" % (name))
        print(sample)

        # First just show what it looks like parsed as a simple dict
        try:
            xml = xmld.parse(sample)
            res = {name: xml}
            print(res)
        except Exception as err:
            print(err, str(err))

        # If we have a schema, try that too
        try:
            if schema is not None:
                schemed = schema.to_dict(sample, decimal_type=float,
                                         validation='lax')
                print(schemed)
        except Exception as err:
            print(str(err))

    print("Done!")