# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 28 Jun 2019
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

import os
import json
import collections.abc
import distutils.util as dut

import xmlschema as xmls

from . import packetizer


def flatten(d, parent_key='', sep='_'):
    """
    Thankfully StackOverflow exists because I'm too tired to write out this
    logic myself and now I can just use this:
    https://stackoverflow.com/a/6027615
    With thanks to:
    https://stackoverflow.com/users/1897/imran
    https://stackoverflow.com/users/1645874/mythsmith
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def parserFlatPacket(hed, msg, schema=None, db=None, debug=False,
                     timestampKey='influx_ts', returnParsed=False):
    """
    """
    # This is really the topic name, so we'll make that the measurement name
    #   for the sake of clarity. It NEEDS to be a list until I fix packetizer!
    meas = [os.path.basename(hed['destination'])]

    # Bail if there's a schema not found; needs expansion here
    if schema is None:
        print("FATAL ERROR: No schema found for topic %s!" % (meas[0]))
        return None

    # In this house, we only store valid packets!
    if isinstance(schema, dict):
        # For now, just be super lazy and try all the versions defined
        #   and see which one sticks. Warning: it might be none of them!
        best = None
        for verKey in schema:
            testSchema = schema[verKey]
            #print("Testing schema:")
            #print(testSchema.url)
            good = testSchema.is_valid(msg)
            if good is True:
                # Override the schema variable with the one that worked
                best = verKey
                #print("Found working schema version: %s" % (verKey))
                break
        if best is not None:
            schema = schema[best]
        else:
            print("Failed to find a working schema :(")
            good = False
            schema = None
    else:
        # print("Schema was not a dict, so no other versions to check.")
        # print(type(schema))
        #
        # We still need this because the version is now used as an extra
        #   database metric postfix if it is there
        best = None
        good = schema.is_valid(msg)

    # A DIRTY DIRTY HACK
    if schema is not None:
        try:
            xmlp = schema.to_dict(msg, decimal_type=float, validation='lax')
            # print(xmlp)
            good = True
        except xmls.XMLSchemaValidationError:
            good = False

    if good is True:
        try:
            # print("Trying to_dict")
            xmlp = schema.to_dict(msg, decimal_type=float, validation='lax')
            # I HATE THIS
            if isinstance(xmlp, tuple):
                xmlp = xmlp[0]

            # Back to normal.
            keys = xmlp.keys()

            fields = {}
            # Store each key:value pairing
            # print("Storing keys")
            # print(keys)
            for each in keys:
                val = xmlp[each]

                # TESTING
                if isinstance(val, dict):
                    flatVals = flatten(val, parent_key=each)
                    fields.update(flatVals)
                else:
                    fields.update({each: val})

            if fields is not None:
                if timestampKey is not None:
                    #print("Specified timestamp key: %s" % (timestampKey))
                    # Find a key that starts with the given timestampKey.  In
                    #   pretty much all the cases I control, this will be
                    #   influx_ts_s or influx_ts_ms
                    # It's assumed that it's already in the right format,
                    #   e.g. INTEGER quantity from the epoch; if it's wrong,
                    #   you'll get influxdb errors in the log and nothing will
                    #   actually be posted!
                    fieldKeys = fields.keys()
                    validTS = True
                    if "%s_s" % (timestampKey) in fieldKeys:
                        timeprec = "s"
                    elif "%s_ms" % (timestampKey) in fieldKeys:
                        timeprec = "ms"
                    elif "%s_ns" % (timestampKey) in fieldKeys:
                        timeprec = "ns"
                    else:
                        # If we end up in here, we didn't find a valid choice
                        #   so set it to None and set defaults
                        validTS = False
                        timeprec = 's'
                        ts = None

                    # There was no good way to set ts above without copying
                    #   and pasting a bunch (at least that I could suss out)
                    #   so check if our flag
                    if validTS is True:
                        try:
                            validTSKey = "%s_%s" % (timestampKey, timeprec)
                            #print("Timestamp key: %s" % (validTSKey))
                            ts = fields.pop(validTSKey)
                        except KeyError:
                            #print("Timestamp key %s not found, using None"
                            #      % (timestampKey))
                            ts = None
                            timeprec = 's'
                else:
                    # Need this for older codes that don't specify this
                    ts = None
                    timeprec = 's'

                # Note: passing ts=None lets python Influx do the timestamp
                # print("Making packet")a
                if best is not None:
                    # This means we had a version of the packet and not
                    #   just the base topic name, so add the version in
                    #   as a postfix for the measurement name.
                    #
                    # For the LDT, this could be a TCS or
                    #   other LabVIEW thing's release version.  For the
                    #   Mesa, this could be a subtype of info stuffed into
                    #   a single topic like *.loisTelemetry
                    #
                    # Also strip out the first letter of the 'best' version
                    #   since it's just a "v" fudged in there.  See
                    #   https://github.com/LowellObservatory/ligmos/issues/21
                    #   for some details on that front.
                    #
                    # Remember; meas is a list and must remain a list!
                    meas = "%s_%s" % (meas[0], best)
                    meas = [meas]

                # Allow a quick exit here after parsing and sorting in case
                #   we need to further organize the results in another function
                #   before sending it off to the databse.  In most cases this
                #   will be False, but it's handy sometimes (like PurpleAir).
                if returnParsed is True:
                    return meas, ts, timeprec, fields
                else:
                    #print("Just before makeInfluxPacket")
                    print(ts, timeprec)
                    packet = packetizer.makeInfluxPacket(meas=meas,
                                                         ts=ts,
                                                         tags=None,
                                                         fields=fields)

                    # print("Packet done")
                    print(packet)

                    # Actually commit the packet. singleCommit opens it,
                    #   writes the packet, and then optionally closes it.
                    if db is not None:
                        print("Sending packet")
                        db.singleCommit(packet, table=db.tablename,
                                        close=True, timeprec=timeprec)
                        # print("Sent!")
        except xmls.XMLSchemaDecodeError as err:
            print(err.message.strip())
            print(err.reason.strip())

        # Added for itteratively testing parsed packets outside of the
        #   usual operational mode (like in toymodels/PacketSchemer)
        if debug is True:
            print(fields)
    else:
        if debug is True:
            print("Packet was bad!?")
            print(hed)
            print(msg)


def parserSimple(hed, msg, db=None, datatype='float'):
    """
    """
    # print("Parsing a simple float message: %s" % msg)
    topic = os.path.basename(hed['destination'])
    if datatype.lower() == 'float':
        try:
            val = float(msg)
        except ValueError as err:
            print(str(err))
            val = -9999.
    elif datatype.lower() == 'string':
        val = str(msg)
    elif datatype.lower() == 'bool':
        try:
            val = dut.strtobool(msg)
        except ValueError as err:
            print(str(err))
            val = -9999
    else:
        print("DEFINITELY NOT YET FINISHED")

    # Make the InfluxDB style packet
    meas = [topic]
    tag = {}

    fields = {"value": val}

    # Make and store the influx packet
    # Note: passing ts=None lets python Influx do the timestamp for you
    packet = packetizer.makeInfluxPacket(meas=meas,
                                         ts=None,
                                         tags=tag,
                                         fields=fields)

    # Actually commit the packet. singleCommit opens it,
    #   writes the packet, and then optionally closes it.
    if db is not None:
        db.singleCommit(packet, table=db.tablename, close=True)


def parseJSON(hed, msg, makeFlat=True, tags={}, db=None, debug=False):
    """
    With makeFlat=True, this will very closely resemble the setup that
    the PWI4 values arrive in and let us use most of the same codepath.

    TODO: Consider the usage of json2xml to scab in schema based checking

    from json2xml import json2xml
    from json2xml.utils import readfromurl, readfromstring, readfromjson

    j = '{"id":1,"current":0.020,"voltage":117.1,"act_power":0.0,
          "aprt_power":2.4,"pf":0.00,"freq":60.0,"calibration":"factory"}'
    d = readfromstring(j)
    d.update({"name": "casspwr1"})
    thisXML = json2xml.Json2xml(d, wrapper="shelly_pwrmon").to_xml()
    ...

    """
    topic = os.path.basename(hed['destination'])

    dat = json.loads(msg)
    if makeFlat is True:
        ndat = flatten(dat, sep=".")
    else:
        ndat = dat

    fdat = {}
    for key in ndat.keys():
        # Just try to make everything a float, and if it fails it's a string!
        try:
            newVal = float(ndat[key])
        except ValueError:
            newVal = str(ndat[key])

        fdat.update({key: newVal})

    # Make the InfluxDB style packet
    meas = [topic]

    # Make and store the influx packet
    # Note: passing ts=None lets python Influx do the timestamp for you
    packet = packetizer.makeInfluxPacket(meas=meas,
                                         ts=None,
                                         tags=tags,
                                         fields=fdat)

    # Actually commit the packet. singleCommit opens it,
    #   writes the packet, and then optionally closes it.
    if db is not None:
        db.singleCommit(packet, table=db.tablename, close=True)
