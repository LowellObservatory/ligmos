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

import xmlschema as xmls
import xmltodict as xmld

# from ligmos import utils


if __name__ == "__main__":
    name = "lorax.command.mount.timo"

    # Use this to read in a schema file; must end in name + ".xsd"
    #   Set basepath to None (or omit it) to search for a ligmos sample
    # schema = utils.xmlschemas.checkSchema(name, basepath='./')

    directSchemaSample = """<?xml version="1.0" encoding="UTF-8"?>
    <xsd:schema elementFormDefault="qualified" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
        <xsd:element name="command">
            <xsd:complexType mixed="true">
                <xsd:sequence>
                    <xsd:element name="command_id" minOccurs="0" type="xsd:normalizedString"/>
                    <xsd:element name="timestamput" minOccurs="0" type="xsd:dateTime"/>
                    <xsd:element name="telescope" minOccurs="0" type="xsd:normalizedString"/>
                    <xsd:element name="device" minOccurs="0">
                        <xsd:complexType mixed="true">
                            <xsd:sequence>
                                <xsd:element name="type" minOccurs="0" type="xsd:normalizedString"/>
                                <xsd:element name="vendor" minOccurs="0" type="xsd:normalizedString"/>
                            </xsd:sequence>
                        </xsd:complexType>
                    </xsd:element>
                    <xsd:element name="command" minOccurs="0" type="xsd:normalizedString"/>
                    <xsd:element name="argument" maxOccurs="unbounded">
                        <xsd:complexType mixed="true">
                            <xsd:sequence>
                                <xsd:element name="value" minOccurs="0" type="xsd:decimal"/>
                            </xsd:sequence>
                            <xsd:attribute name="type" type="xsd:normalizedString" use="required"/>
                        </xsd:complexType>
                    </xsd:element>
                </xsd:sequence>
            </xsd:complexType>
        </xsd:element>
    </xsd:schema>
    """
    schema = xmls.XMLSchema(directSchemaSample)

    # Use this to read in a sample file; must end in name + ".xml"
    #   Set basepath to None (or omit it) to search for a ligmos sample
    # sample = utils.xmlschemas.checkSample(name, basepath='./')

    # You can also specify just a full string if you're playing with things
    sample = """<?xml version="1.0" encoding="utf-8"?>
    <command>
        <command_id>2316ff98-1e4a-4564-bfb2-59f79cb6ae0a</command_id>
        <timestamput>2022-03-14T03:00:00.0000+00:00</timestamput>
        <telescope>TiMo</telescope>
        <device>
            <type>mount</type>
            <vendor>planewave</vendor>
        </device>
        <command>gotoAltAz</command>
        <argument type="elevation">
            <value>45.0</value>
        </argument>
        <argument type="azimuth">
            <value>200.0</value>
        </argument>
    </command>"""

    # Quick check to make sure there's an actual sample to assess; if the
    #   sample isn't found, it'll be the null string
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
