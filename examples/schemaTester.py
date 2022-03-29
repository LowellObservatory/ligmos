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

from ligmos import utils


if __name__ == "__main__":
    name = "lig.MrFreeze.cmd"

    schema = utils.xmlschemas.checkSchema(name)
    sample = utils.xmlschemas.checkSample(name)

    # sample = """Lois Telemetry Initialized"""

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
                good = schema.is_valid(sample)
                if good is True:
                    xmlp = schema.to_dict(sample, decimal_type=float,
                                          validation='lax')
                    # I HATE THIS
                    if isinstance(xmlp, tuple):
                        xmlp = xmlp[0]

                    # Back to normal.
                    keys = xmlp.keys()

                    fields = {}
                    # Store each key:value pairing
                    print("Storing keys")
                    print(keys)
                    for each in keys:
                        val = xmlp[each]
                        fields.update({each: val})

                    print(fields)
                else:
                    # This returns nothing, but will raise errors.
                    #   They'll be caught in the bulk/blank Exception below.
                    schema.validate(sample)
                    print("Failed validation against the schema!")
        except Exception as err:
            print(str(err))

    print("Done!")
