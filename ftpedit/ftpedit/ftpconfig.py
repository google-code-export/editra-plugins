###############################################################################
# Name: ftpconfig.py                                                          #
# Purpose: Ftp Configuration Window.                                          #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""Ftp Configuration Window"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import wx

#-----------------------------------------------------------------------------#

class FtpConfigDialog(wx.Dialog):
    def __init__(self, parent, title=u''):
        wx.Dialog.__init__(self, parent, title=title)

        # Attributes
        self._panel = FtpConfigPanel(self)

        # Layout
        self.__DoLayout()

        # Event Handlers
        

    def __DoLayout(self):
        """Layout the Dialog"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._panel, 1, wx.EXPAND)
        self.SetSizer(sizer)

#-----------------------------------------------------------------------------#

class FtpConfigPanel(wx.Panel):
    """Configuration Panel"""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Attributes
        
        # Layout
        self.__DoLayout()

        # Event Handlers
        

    def __DoLayout(self):
        """Layout the Dialog"""
        pass

#-----------------------------------------------------------------------------#
