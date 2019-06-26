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

from requests.exceptions import ConnectionError as RCE

try:
    import influxdb
    from influxdb import InfluxDBClient
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

    def writeToDB(self, vals, table=None, debug=False):
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
                        res = self.client.write_points(vals)
                    else:
                        res = self.client.write_points(vals, database=table)
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
                print("INFLUXDB ERROR")
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

    def singleCommit(self, packet, table=None, debug=False, close=True):
        if self.client is not None:
            self.closeDB()
        self.openDB()
        self.writeToDB(packet, table=table, debug=debug)
        if close is True:
            self.closeDB()
