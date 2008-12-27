###############################################################################
# Name: ftpclient.py                                                          #
# Purpose: Ftp client for managing connections, downloads, uploads.           #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""Ftp Client

Ftp client class for managing connections, uploads, and downloads.

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import re
import ftplib
import socket

#-----------------------------------------------------------------------------#

class FtpClient(ftplib.FTP):
    """Ftp Client"""
    def __init__(self, host=u'', port=21):
        """Create an ftp client object
        @keyword host: host name/ip
        @keyword port: port number

        """
        ftplib.FTP.__init__(self, host)

        # Attributes
        self._default = u''     # Default path
        self._host = host       # Host name
        self._port = port       # Port number
        self._active = False    # Connected?
        self._data = list()     # recieved data
        self._lasterr = None    # Last error

        # Setup
        self.set_pasv(True) # Use passive mode for now (configurable later)

    def Connect(self, user, password):
        """Connect to the site
        @param user: username
        @param password: password

        """
        try:
            self.connect(self._host, self._port)
            self.login(user, password)
        except socket.error, msg:
            self._lasterr = msg
            return False
        else:
            self._active = True

        return True

    def Disconnect(self):
        """Disconnect from the site"""
        try:
            if self._active:
                self.abort()
            self.quit()
            self._active = False
        except:
            pass

    def GetFileList(self, path):
        """Get list of files at the given path
        @return: list of strings

        """
        try:
#            self.cwd('public_html')
            code = self.retrlines('LIST', lambda data: self._data.append(data))
        except Exception, msg:
            print "ERR GETFILELIST", msg

        rval = list(data)
        self._data = list()
        return rval

    def GetLastError(self):
        """Get the last error that occured
        @return: Exception

        """
        return self._lasterr

    def IsActive(self):
        """Does the client have an active connection
        @return: bool

        """
        return self._active

    def MkDir(self, dname):
        """Make a new directory at the current path
        @param dname: string

        """
        raise NotImplementedError

    def SetDefaultPath(self, dpath):
        """Set the default path
        @param dpath: string

        """
        self._default = dpath

    def SetHostname(self, hostname):
        """Set the host name
        @param hostname: string

        """
        self._host = hostname

    def SetPort(self, port):
        """Set the port to connect to
        @param port: port number (int)

        """
        self._port = port

#-----------------------------------------------------------------------------#

def ParseFtpOutput(lines):
    """parse output from the ftp command
    @param lines: list of strings

    """
    pass
