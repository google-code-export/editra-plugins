###############################################################################
# Name: ftpwindow.py                                                          #
# Purpose: Ftp Window                                                         #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""Ftp Window"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import wx
import wx.lib.mixins.listctrl as listmix

# Editra Libraries
import ed_glob
import eclib.ctrlbox as ctrlbox
import eclib.platebtn as platebtn
import eclib.elistmix as elistmix

#-----------------------------------------------------------------------------#
# Globals
ID_SITES = wx.NewId()
ID_CONNECT = wx.NewId()
ID_DISCONNECT = wx.NewId()

_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class FtpWindow(ctrlbox.ControlBox):
    """Ftp file window"""
    def __init__(self, parent, id=wx.ID_ANY):
        ctrlbox.ControlBox.__init__(self, parent, id)

        # Attributes
        self._sites = None    # wx.Choice
        self._username = None # wx.TextCtrl
        self._password = None # wx.TextCtrl

        # Layout
        self.__DoLayout()

        # Event Handlers
        

    def __DoLayout(self):
        """Layout the window"""
        cbar = ctrlbox.ControlBar(self, style=ctrlbox.CTRLBAR_STYLE_GRADIENT)

        # Preferences
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_PREF), wx.ART_MENU)
        btn = platebtn.PlateButton(cbar, bmp=bmp, style=platebtn.PB_STYLE_NOBG)
        cbar.AddControl(btn, wx.ALIGN_LEFT)

        # Sites
        cbar.AddControl(wx.StaticText(cbar, label=_("Sites:")), wx.ALIGN_LEFT)
        self._sites = wx.Choice(cbar, ID_SITES)
        cbar.AddControl(self._sites, wx.ALIGN_LEFT)

        # Username
        cbar.AddControl(wx.StaticText(cbar, label=_("Username:")), wx.ALIGN_LEFT)
        self._username = wx.TextCtrl(cbar)
        cbar.AddControl(self._username, wx.ALIGN_LEFT)

        # Password
        cbar.AddControl(wx.StaticText(cbar, label=_("Password:")), wx.ALIGN_LEFT)
        self._password = wx.TextCtrl(cbar, style=wx.TE_PASSWORD)
        cbar.AddControl(self._password, wx.ALIGN_LEFT)

        # Connect
        cbar.AddStretchSpacer()
        cbar.AddControl(platebtn.PlateButton(cbar, label=_("Connect")), wx.ALIGN_RIGHT)

        # Setup Window
        self.SetControlBar(cbar, wx.TOP)
        self.SetWindow(FtpList(self, wx.ID_ANY))

#-----------------------------------------------------------------------------#

class FtpList(listmix.ListCtrlAutoWidthMixin,
              elistmix.ListRowHighlighter,
              wx.ListCtrl):
    """Ftp File List"""
    def __init__(self, parent, id=wx.ID_ANY):
        wx.ListCtrl.__init__(self, parent, id, style=wx.LC_ICON|wx.LC_REPORT) 
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        elistmix.ListRowHighlighter.__init__(self)
        self.InsertColumn(0, _("Filename"))
        self.InsertColumn(1, _("Size"))
        self.InsertColumn(2, _("Modified"))

        self.setResizeColumn(0)

