# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on Wed Jan 31 14:43:10 2018
#
#  @author: rhamilton

from __future__ import division, print_function, absolute_import

import time
import socket

import paramiko
# from paramiko import SSHException, AuthenticationException

from . import multialarm


class SSHWrapper():
    """
    """
    def __init__(self, host='', username='',
                 port=22, password='', retries=5, timeout=30.,
                 connectOnInit=True):
        self.host = host
        self.username = username
        self.port = port
        self.passw = password
        self.retries = retries
        self.timeout = timeout

        # Paramiko stuff
        self.ssh = paramiko.SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sftp = None

        if connectOnInit is True:
            self.connect()

    def connect(self, maxtime=60):
        """
        """
        # Hardcoded wait/timeout of 10 seconds for SSH connection
        #   BUT, that timeout is pretty janky and doesn't always
        #   work or even timeout properly so that's why we have
        #   a multialarm.Timeout wrapper on everything here below
        sshitimeout = 10

        # Counter and flag related to retries
        ctries = 0
        self.success = False

        try:
            # Set a timer for the whole connect/retry process
            with multialarm.Timeout(id_="SSHConnTotal", seconds=maxtime):
                while ctries < self.retries and self.success is False:
                    try:
                        self.ssh.connect(self.host, port=self.port,
                                         username=self.username,
                                         password=self.passw,
                                         timeout=sshitimeout,
                                         banner_timeout=sshitimeout,
                                         auth_timeout=sshitimeout)
                        print("SSH connection to %s opened" % (self.host))
                        self.success = True
                    except socket.error as err:
                        # Using base socket class to try to catch all the
                        #   bad stuff that could go wrong...
                        #   paramiko documentation kinda sucks here.
                        print("SSH connection to %s failed!" % (self.host))
                        print(str(err))
                        print("Retry %d" % (ctries))
                        ctries += 1
                        if ctries >= self.retries:
                            self.ssh = None
                        else:
                            time.sleep(3)
        except multialarm.TimeoutError as err:
            # Only deal with our specific SSH timeout error
            if err.id_ == "SSHConnTotal":
                print(str(err))
                ctries += 1
                if ctries >= self.retries:
                    self.ssh = None
                else:
                    time.sleep(3)

    def closeConnection(self, timeout=3):
        """
        """
        try:
            with multialarm.Timeout(id_="SSHClose", seconds=timeout):
                if self.ssh is not None:
                    self.ssh.close()
        except multialarm.TimeoutError as err:
            if err.id_ == "SSHClose":
                self.ssh = None
                print("SSH connection close failed? WTF?")

    def openSFTP(self, timeout=30.):
        """
        """
        try:
            with multialarm.Timeout(id_="SFTPOpen", seconds=timeout):
                if self.ssh is not None:
                    self.sftp = self.ssh.open_sftp()
        except multialarm.TimeoutError as err:
            if err.id_ == "SFTPOpen":
                self.sftp = None
                print("Could not open SFTP connection")

    def closeSFTP(self, timeout=3.):
        """
        """
        try:
            with multialarm.Timeout(id_="SFTPClose", seconds=timeout):
                if self.sftp is not None:
                    self.sftp.close()
                    self.sftp = None
        except multialarm.TimeoutError as err:
            if err.id_ == "SFTPClose":
                self.sftp = None
                print("Could not close SFTP connection")

    def getFile(self, lfile, rfile, timeout=120.):
        """
        """
        try:
            with multialarm.Timeout(id_="SFTPXfer", seconds=timeout):
                if self.sftp is not None:
                    # Transfer the file from the remote to local locations
                    self.sftp.get(rfile, lfile)
                    return True
        except multialarm.TimeoutError as err:
            if err.id_ == "SFTPXfer":
                self.sftp = None
                print("File transfer took too long!")
                return False

    def putFile(self, lfile, rfile, timeout=120.):
        """
        From the Paramiko SFTP docs:

        Note that the filename should be included.
        Only specifying a directory may result in an error.
        """
        try:
            with multialarm.Timeout(id_="SFTPXfer", seconds=timeout):
                if self.sftp is not None:
                    # Transfer the file from the local location to the remote
                    self.sftp.put(lfile, rfile)
                    return True
        except multialarm.TimeoutError as err:
            if err.id_ == "SFTPXfer":
                self.sftp = None
                print("File transfer took too long!")
                return False

    def sendCommand(self, command, debug=False):
        """
        """
        ses, stdout_data, stderr_data = None, None, None
        if self.ssh:
            stdin, stdout, stderr = self.ssh.exec_command(command)
            # Close stdin since we're not using it
            stdin.close()

            # Just use the channel object in a simple way.
            #   Went through many itterations with buffered reads,
            #   all of which failed eventually in some obscure way.
            #   This is way easier for now and this should be visited
            #   if things start to drop out in the future.
            stdout_data = []
            # If stuff gets put onto stderr, it could block...I think.
            for line in stdout:
                if debug is True:
                    print(line)
                stdout_data.append(line)

            stdout_data = "".join(stdout_data)
            stderr_data = []
            ses = stdout.channel.exit_status

            stdout.close()
            stderr.close()
        else:
            print("SSH connection not opened!")
            print("Trying to open it one more time...")
            # Open once more

        return ses, stdout_data, stderr_data
