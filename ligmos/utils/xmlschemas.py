# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 16 Aug 2021
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

from os.path import basename

import xmlschema as xmls
import pkg_resources as pkgr


def findNamedSchema(schemaList, schemaDict, tname):
    """
    """
    try:
        schema = schemaDict[tname]
    except KeyError:
        # If we didn't get it right on the first try, fall
        #   back to a full search of the schemas using the
        #   current tname as a prefix. Eventually this can
        #   be optimized at initialization to make a map of
        #   topic names to schemas/parsers once instead of
        #   every single time, but that's 2.0 talk.
        schema = [e for e in schemaList if tname.lower().startswith(e)]

        # Some last minute checks
        if schema == []:
            print("WARNING - No schema found!")
            schema = None
        else:
            # If there are multiple results, warn about it
            #   but then just take the first
            if len(schema) > 1:
                print("WARNING - Multiple matching schemas!")
                print(schema)

            schemaSelected = schema[0]
            schema = schemaDict[schemaSelected]

    print("Schema found:", schema)

    return schema


def checkSchema(topicname):
    """
    """
    # Put together the expected schema name
    sn = 'schemas/' + topicname + '.xsd'
    try:
        # Define the schema we'll use to convert datatypes. If it doesn't
        #   exist, catch the exception and return 'None' to show that
        #   the schema didn't exist where it was expected
        sf = pkgr.resource_filename('ligmos', sn)
        schema = xmls.XMLSchema(sf)
        return schema
    except xmls.exceptions.XMLSchemaException as err:
        print("Problem with schema for topic %s!" % (topicname))
        print(str(err))
        return None
    except OSError as err:
        print("Schema %s not found!" % (sf))
        return None


def checkSample(topicname):
    """
    """
    # Put together the expected schema name
    sn = 'schemas/xmlsamples/' + topicname + '.xml'
    try:
        # Define the schema we'll use to convert datatypes. If it doesn't
        #   exist, catch the exception and return 'None' to show that
        #   the schema didn't exist where it was expected
        sf = pkgr.resource_filename('ligmos', sn)
        xmlstr = ""
        with open(sf, 'r') as f:
            xmlstr = f.read()

        return xmlstr
    except xmls.exceptions.XMLSchemaException:
        print("Sample for topic %s not found!" % (topicname))
        return ""
    except (IOError, OSError):
        print("Sample for topic %s not found!" % (topicname))
        return ""


def schemaDicter():
    """
    Grab all of the schemas in the package directory and return
    a dict organized by topic name.
    """
    sdict = {}

    # Get the list of everything in the schema repo
    allschemas = pkgr.resource_listdir('ligmos', 'schemas')

    for tsch in allschemas:
        spath = "%s/%s" % ('schemas', tsch)
        schname = basename(tsch)

        # Strip the file extension off of it!
        schname = schname[:-4]

        if pkgr.resource_isdir('ligmos', spath):
            print("%s is a directory! Skipping it." % (tsch))
        else:
            print("%s is a potential schema! Looking at it." % (schname))

            # Try to peel off a version tag, if there is one. It needs to be a
            #   very specific format!
            # broker.topic.name.vX-Y-Z.xsd
            schparts = schname.split(".")
            # if it starts with "v" AND also has underscores, it's probably
            #   a tag.  It's dumb but it works for now. Could be improved.
            if schparts[-1].startswith("v"):
                if "_" in schparts[-1]:
                    vtag = schparts[-1]
                    origtag = schname[:-len(vtag)-1]
                    # Some more transformations to clean it up to what should
                    #   be in the packets themselves
                    vtag = vtag.replace("_", ".")
            else:
                origtag = schname
                vtag = None

            try:
                # Define the schema we'll use to convert datatypes
                sf = pkgr.resource_filename('ligmos', spath)
                schema = xmls.XMLSchema(sf)
                # Deal with our multi-version case
                if vtag is not None:
                    print("Storing %s %s" % (origtag, vtag))
                    versionedSchema = {vtag: schema}
                    # Make sure that if we have a version tag, we don't
                    #   clobber something else already stored
                    if origtag in sdict.keys():
                        existingEntry = sdict[origtag]
                        existingEntry.update(versionedSchema)
                        sdict.update({origtag: existingEntry})
                    else:
                        sdict.update({origtag: versionedSchema})
                else:
                    sdict.update({origtag: schema})
            except xmls.exceptions.XMLSchemaException as err:
                print("xmlschema error!")
                print(str(err))
                print("Schema for topic %s has been abandoned!" % (schname))
            except xmls.etree.ParseError as err:
                print("xmlschema error!")
                print(str(err))
                print("Schema for topic %s has been abandoned!" % (schname))

    return sdict
