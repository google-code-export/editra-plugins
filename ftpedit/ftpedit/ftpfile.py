###############################################################################
# Name: ftpfile.py                                                            #
# Purpose: Ftp file layer                                                     #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""Ftp File

Classes and utilities for abstracting files operations over ftp.

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import os

# Editra Libraries
import ed_txt
from util import Log

# Local Imports
import ftpclient

#-----------------------------------------------------------------------------#

class FtpFile(ed_txt.EdFile):
    def __init__(self, ftppath, sitedata, path='', modtime=0):
        """Create the FtpFile
        @param ftppath: path to file on ftp server
        @param sitedata: site login data
        @keyword path: on disk path (used by EdFile)
        @keyword modtime: last mod time (used by EdFile)

        """
        ed_txt.EdFile.__init__(self, path, modtime)

        # Attributes
        self._client = ftpclient.FtpClient(None)
        self._ftp = True
        self.ftppath = ftppath
        self._site = sitedata   # dict(url, port, user, pword, path, enc)

        # Setup
        self.SetEncoding(self._site['enc'])

    def __del__(self):
        """Cleanup the temp file"""
        if self._ftp:
            # Only remove if its the temp file
            os.remove(self.GetPath())

        if self._client.IsActive():
            self._client.Disconnect()

    def DoFtpUpload(self):
        """Upload the contents of the on disk temp file to the server"""
        connected = self._client.IsActive()
        if not connected:
            self._client.SetHostname(self._site['url'])
            self._client.SetPort(self._site['port'])
            connected = self._client.Connect(self._site['user'],
                                             self._site['pword'])

        if not connected:
            # TODO: report error to upload
            err = self._client.GetLastError()
            Log("[ftpedit][err] DoFtpUpload: %s" % err)
        else:
            self._client.Upload(self.GetPath(), self.ftppath)
            # TODO: notify of completion

    def GetFtpPath(self):
        """Get the ftp path
        @return: string

        """
        return self.ftppath

    def GetSiteData(self):
        """Get the ftp site data that this file belongs to
        @return: dict(url, port, user, pword, path, enc)

        """
        return self._site

    def SetFilePath(self, path):
        """Change the file path. Changing the path on an ftp file
        will disassociate it with the ftp site turning it into a regular
        file.
        @param path: string

        """
        cpath = self.GetPath()
        if path != cpath:
            super(FtpFile, self).SetFilePath(path)
            self._ftp = False

    def Write(self, value):
        """Override EdFile.Write to trigger an upload
        @param value: string

        """
        # Save the local file
        super(FtpFile, self).Write(value)

        # Upload the file to the server
        if self._ftp:
            t = ftpclient.FtpThread(None, self.DoFtpUpload,
                                    ftpclient.EVT_FTP_UPLOAD)
            t.start()

#-----------------------------------------------------------------------------#


