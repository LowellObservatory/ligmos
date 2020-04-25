# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on Thu Feb 22 20:05:07 2018
#
#  @author: rhamilton

from __future__ import division, print_function, absolute_import

import json
import datetime as dt

import pytz
import numpy as np
import pandas as pd

from requests.exceptions import ConnectionError as RCE

try:
    import influxdb
    from influxdb import InfluxDBClient
    from influxdb import DataFrameClient
    from influxdb.exceptions import InfluxDBClientError
except (ImportError, ModuleNotFoundError) as err:
    influxdb = None


class influxobj():
    """
    Creates an InfluxDB database access object, specific to a database name.

    """
    def __init__(self, tablename=None, connect=True,
                 host='localhost', port=8086,
                 user='marty', pw='mcfly'):
        self.host = host
        self.port = port
        self.username = user
        self.password = pw
        self.tablename = tablename

        # Reminder; influxdb is the actual import, this makes sure it worked
        if connect is True and influxdb is not None:
            self.openDB()
        else:
            self.client = None

    def alterRetention(self, pname='Hold26w', duration='26w'):
        """
        DEPRECIATED

        Changing retentions is not to be done so lightly, since you need
        to remember to move the data from the previous one into the new one
        as well.

        Now it's just a noop, basically
        """
        pass

    def openDB(self):
        """
        """
        if influxdb is not None:
            try:
                self.client = InfluxDBClient(self.host, self.port,
                                             username=self.username,
                                             password=self.password,
                                             database=self.tablename)
            except Exception as err:
                self.client = None
                print("Could not open database %s:\n%s" % (self.tablename,
                                                           str(err)))
        else:
            print("InfluxDB-python not found or server not running!")

    def writeToDB(self, vals, table=None, timeprec='s', debug=False):
        """
        Given an opened InfluxDBClient, write stuff to the given dbname.

        BUG: InfluxDB errors are getting returned, not caught. Don't know why.
        e.g.
        400: {"error":"field type conflict: input field \"ping\" on
              measurement \"PingResults\" is type integer, already exists as
              type float"}
        """
        # Make sure we're actually connected first
        if self.client is not None:
            res = False
            try:
                if debug is True:
                    print("Trying to write_points")

                try:
                    if table is None:
                        res = self.client.write_points(vals,
                                                       time_precision=timeprec)
                    else:
                        res = self.client.write_points(vals, database=table,
                                                       time_precision=timeprec)
                except InfluxDBClientError as err:
                    if err.code == 403:
                        print("Authentication error! %s" % (err.content))
                        # Clear the client to make other stuff break
                        self.client = None
                        res = False
                    if err.code == 400:
                        # This usually means a database table wasn't specified
                        #   or there was a type mismatch. Either way,
                        #   NO BUENO
                        print(err.content)
                        self.client = None
                        res = False
            except RCE as err:
                print("Fatal Connection Error!")
                print("Is InfluxDB running?")
                # sys.exit(-1)
            except InfluxDBClientError as err:
                print("ERROR: write_points to InfluxDB Failed!")
                # If we're here, bad things happened with the database.
                try:
                    econd = json.loads(err.content)
                    print(econd['error'])
                    print(vals)
                except Exception as errp:
                    print(str(err))
                    print(str(errp))
                    print(vals)
                    print("Unparsable error condition from Influx :(")
            if res is False:
                print("INFLUXDB ERROR. Check above for more details :(")
        else:
            print("Error: InfluxDBClient not connected!")

    def closeDB(self):
        """
        """
        if self.client is not None:
            try:
                self.client.close()
            except Exception as err:
                print(str(err))

    def connect(self):
        # Just a stub in case I can't remember...
        self.openDB()

    def write(self, vals, debug=False):
        # Just a stub in case I can't remember...
        self.writeToDB(vals, debug=debug)

    def disconnect(self):
        # Just a stub in case I can't remember...
        self.closeDB()

    def close(self):
        # Just a stub in case I can't remember...
        self.closeDB()

    def singleCommit(self, packet, table=None, timeprec='s',
                     debug=False, close=True):
        if self.client is not None:
            self.closeDB()
        self.openDB()
        self.writeToDB(packet, table=table, timeprec=timeprec, debug=debug)
        if close is True:
            self.closeDB()


def queryConstructor(dbq, debug=False):
    """
    dbq is type databaseQuery, which includes databaseConfig as
    dbq.db.  More info in 'confHerder'.

    dtime is time from present (in hours) to query back

    Allows grouping of the results by a SINGLE tag with multiple values.
    No checking if you want all values for a given tag, so be explicit for now.
    """
    if isinstance(dbq.rangehours, str):
        try:
            dtime = int(dbq.rangehours)
        except ValueError:
            print("Can't convert %s to int!" % (dbq.rangehours))
            dtime = 1

    if dbq.database.type.lower() == 'influxdb':
        if debug is True:
            print("Searching for %s in %s.%s on %s:%s" % (dbq.fields,
                                                          dbq.tablename,
                                                          dbq.metricname,
                                                          dbq.database.host,
                                                          dbq.database.port))

        # Some renames since this was adapted from an earlier version
        tagnames = dbq.tagnames
        if tagnames is not None:
            tagvals = dbq.tagvals
        else:
            tagvals = []

        # TODO: Someone should write a query validator to make sure
        #   this can't run amok.  For now, make sure the user has
        #   only READ ONLY privileges to the database in question!!!
        query = 'SELECT'
        if isinstance(dbq.fields, list):
            for i, each in enumerate(dbq.fields):
                # Catch possible fn/dn mismatch
                try:
                    query += ' "%s" AS "%s"' % (each.strip(),
                                                dbq.fieldlabels[i])
                except IndexError:
                    query += ' "%s"' % (each.strip())
                if i != len(dbq.fields)-1:
                    query += ','
                else:
                    query += ' '
        else:
            if dbq.fieldlabels is not None:
                query += ' "%s" AS "%s" ' % (dbq.fields, dbq.fieldlabels)
            else:
                query += ' "%s" ' % (dbq.fields)

        query += 'FROM "%s"' % (dbq.metricname)
        query += ' WHERE time > now() - %02dh' % (dtime)

        if tagvals != []:
            query += ' AND ('
            if isinstance(dbq.tagvals, list):
                for i, each in enumerate(tagvals):
                    query += '"%s"=\'%s\'' % (tagnames, each.strip())

                    if i != len(tagvals)-1:
                        query += ' OR '
                query += ') GROUP BY "%s"' % (tagnames)
            else:
                # If we're here, there was only 1 tag value so we don't need
                #   to GROUP BY anything
                query += '"%s"=\'%s\')' % (tagnames, tagvals)

        return query


def getResultsDataFrame(query, debug=False):
    """
    Attempts to distinguish queries that have results grouped by a tag
    vs. those which are just of multiple fields. May be buggy still.
    """
    querystr = queryConstructor(query, debug=debug)

    # Line length/clarity control
    db = query.database
    idfc = DataFrameClient(host=db.host, port=db.port,
                           username=db.user,
                           password=db.password,
                           database=query.tablename)

    results = idfc.query(querystr)

    # results is a dict of dataframes, but it's a goddamn mess. Clean it up.
    betterResults = {}

    # Get the names of the expected columns
    expectedCols = query.fieldlabels

    if results != {}:
        # If all went well, results.keys() should be the same as
        #   query.metricname; if I do this right I can hopefully
        #   ditch the first for loop below?
        # rframe = results[query.metricname]

        for rkey in results.keys():
            # If you had a tag that you "GROUP BY" in the query, you'll now
            #   have a tuple of the metric name and the tag + value pair.
            #   If you had no tag to group by, you'll have just the
            #   flat result.
            if isinstance(rkey, tuple):
                # Someone tell me again why Pandas is so great?
                #   I suppose it could be jankiness in influxdb-python?
                #   This magic 'tval' line below is seriously dumb though.
                tval = rkey[1][0][1]
                dat = results[rkey]
                betterResults.update({tval: dat})
            elif isinstance(rkey, str):
                betterResults = results[rkey]

        # Check to make sure all of the expected columns are in our frame
        cols = betterResults.columns.to_list()
        for ecol in expectedCols:
            if ecol not in cols:
                print("Missing column %s in result set!" % (ecol))
                betterResults[ecol] = None
            else:
                print("Found column %s in result set." % (ecol))
    else:
        # This means that the query literally returned nothing at all, so
        #   we have to make the expected DataFrame ourselves so others
        #   don't crash outright. We need to make sure the index of the
        #   dataframe is of type DateTimeIndex as well so future screening
        #   doesn't barf due to missing methods, too.  Lil' bit hackish.
        print("Query returned no results!")

        then = dt.datetime.strptime("1983-04-15T02:00", "%Y-%m-%dT%H:%M")
        then = then.replace(tzinfo=pytz.UTC)

        betterResults = pd.DataFrame()
        dummyFrame = pd.Series([np.nan], index=[then])

        if isinstance(expectedCols, str):
            betterResults[expectedCols] = dummyFrame
        elif isinstance(expectedCols, list):
            for ecol in expectedCols:
                betterResults[ecol] = dummyFrame

    # This is at least a little better
    return betterResults
