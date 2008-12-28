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
import ed_msg
from profiler import Profile_Get, Profile_Set
import eclib.ctrlbox as ctrlbox
import eclib.platebtn as platebtn
import eclib.elistmix as elistmix

# Local Imports
import IconFile
import ftpconfig
import ftpclient

#-----------------------------------------------------------------------------#
# Globals
CONFIG_KEY = u"FtpEdit.Sites"
ID_SITES = wx.NewId()
ID_CONNECT = wx.NewId()

_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class FtpWindow(ctrlbox.ControlBox):
    """Ftp file window"""
    def __init__(self, parent, id=wx.ID_ANY):
        ctrlbox.ControlBox.__init__(self, parent, id)

        # Attributes
        self._mw = self.__FindMainWindow()
        self._config = ftpconfig.ConfigData
        self._config.SetData(Profile_Get(CONFIG_KEY, default=dict()))
        self._connected = False
        self._client = ftpclient.FtpClient(self)
        self._files = list()

        # Ui controls
        self._cbar = None     # ControlBar
        self._list = None     # FtpList
        self._sites = None    # wx.Choice
        self._username = None # wx.TextCtrl
        self._password = None # wx.TextCtrl

        # Layout
        self.__DoLayout()
        self.EnableControls(bool(self._config.GetCount()))
        self.RefreshControlBar()

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnButton, id=wx.ID_PREFERENCES)
        self.Bind(wx.EVT_BUTTON, self.OnButton, id=ID_CONNECT)
        self.Bind(wx.EVT_CHOICE, self.OnChoice, id=ID_SITES)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(ftpclient.EVT_FTP_REFRESH, self.OnRefresh)
        self.Bind(ftpclient.EVT_FTP_DOWNLOAD, self.OnDownload)

        # Editra Message Handlers
        ed_msg.Subscribe(self.OnThemeChanged, ed_msg.EDMSG_THEME_CHANGED)
        ed_msg.Subscribe(self.OnCfgUpdated, ftpconfig.EDMSG_FTPCFG_UPDATED)

    def __del__(self):
        """Cleanup"""
        ed_msg.Unsubscribe(self.OnThemeChanged)
        ed_msg.Unsubscribe(self.OnCfgUpdated)

    def __DoLayout(self):
        """Layout the window"""
        self._cbar = ctrlbox.ControlBar(self, style=ctrlbox.CTRLBAR_STYLE_GRADIENT)
        if wx.Platform == '__WXGTK__':
            self._cbar.SetWindowStyle(ctrlbox.CTRLBAR_STYLE_DEFAULT)

        # Preferences
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_PREF), wx.ART_MENU)
        btn = platebtn.PlateButton(self._cbar, wx.ID_PREFERENCES,
                                   bmp=bmp, style=platebtn.PB_STYLE_NOBG)
        btn.SetToolTipString(_("Configuration"))
        self._cbar.AddControl(btn, wx.ALIGN_LEFT)

        # Sites
        self._cbar.AddControl(wx.StaticText(self._cbar, label=_("Sites:")), wx.ALIGN_LEFT)
        self._sites = wx.Choice(self._cbar, ID_SITES)
        self._cbar.AddControl(self._sites, wx.ALIGN_LEFT)

        # Username
        self._cbar.AddControl(wx.StaticText(self._cbar, label=_("Username:")), wx.ALIGN_LEFT)
        self._username = wx.TextCtrl(self._cbar)
        self._cbar.AddControl(self._username, wx.ALIGN_LEFT)

        # Password
        self._cbar.AddControl(wx.StaticText(self._cbar, label=_("Password:")), wx.ALIGN_LEFT)
        self._password = wx.TextCtrl(self._cbar, style=wx.TE_PASSWORD)
        self._cbar.AddControl(self._password, wx.ALIGN_LEFT)

        # Connect
        self._cbar.AddStretchSpacer()
        bmp = IconFile.Connect.GetBitmap()
        connect = platebtn.PlateButton(self._cbar, ID_CONNECT, bmp=bmp,
                                       label=_("Connect"),
                                       style=platebtn.PB_STYLE_NOBG)
        self._cbar.AddControl(connect, wx.ALIGN_RIGHT)

        # Setup Window
        self.SetControlBar(self._cbar, wx.TOP)
        self._list = FtpList(self, wx.ID_ANY)
        self.SetWindow(self._list)

    def __FindMainWindow(self):
        """Find the mainwindow of this control
        @return: MainWindow or None

        """
        def IsMainWin(win):
            """Check if the given window is a main window"""
            return getattr(tlw, '__name__', '') == 'MainWindow'

        tlw = self.GetTopLevelParent()
        if IsMainWin(tlw):
            return tlw
        elif hasattr(tlw, 'GetParent'):
            tlw = tlw.GetParent()
            if IsMainWin(tlw):
                return tlw

        return None

    def _StartBusy(self, busy=True):
        """Start/Stop the main windows busy indicator
        @keyword busy: bool

        """
        pid = self._mw.GetId()
        if busy:
            # Pulse
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (pid, True))
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_STATE, (pid, -1, -1))
        else:
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_STATE, (pid, 0, 0))

    def EnableControls(self, enable=True):
        """Enable or disable controls in the control bar
        @keyword enable: bool

        """
        for child in self._cbar.GetChildren():
            if child.GetId() != wx.ID_PREFERENCES:
                child.Enable(enable)

    def OnButton(self, evt):
        """Handle Button click events"""
        e_id = evt.GetId()
        if e_id == ID_CONNECT:
            e_obj = evt.GetEventObject()
            if self._connected:
                # Disconnect from server
                self._connected = False
                self._client.Disconnect()
                e_obj.SetLabel(_("Connect"))
                e_obj.SetBitmap(IconFile.Connect.GetBitmap())
                self._list.DeleteAllItems()
            else:
                # Connect to site
                user = self._username.GetValue().strip()
                password = self._password.GetValue().strip()
                site = self._sites.GetStringSelection()
                self._connected = True
                e_obj.SetLabel(_("Disconnect"))
                e_obj.SetBitmap(IconFile.Disconnect.GetBitmap())

                # TODO: start ftp connection thread
                url = self._config.GetSiteHostname(site)
                port = self._config.GetSitePort(site)
                self._client.SetDefaultPath(self._config.GetSitePath(site))
                self._client.SetHostname(url)
                self._client.SetPort(port)
                connected = self._client.Connect(user, password)
                if not connected:
                    # TODO handle errors
                    print self._client.GetLastError()
                else:
                    self._StartBusy(True)
                    self._client.RefreshPath()

            self._cbar.Layout()
        elif e_id == wx.ID_PREFERENCES:
            # Show preferences dialog
            app = wx.GetApp()
            win = app.GetWindowInstance(ftpconfig.FtpConfigDialog)
            if win is None:
                config = ftpconfig.FtpConfigDialog(self._mw,
                                                   _("Ftp Configuration"))
                config.CentreOnParent()
                config.Show()
            else:
                win.Raise()
        else:
            evt.Skip()

    def OnChoice(self, evt):
        """Handle Choice Control Events"""
        if evt.GetId() == ID_SITES:
            # Change the current Site
            site = self._sites.GetStringSelection()
            password = self._config.GetSitePassword(site)
            user = self._config.GetSiteUsername(site)
            self._username.SetValue(user)
            self._password.SetValue(password)
        else:
            evt.Skip()

    def OnCfgUpdated(self, msg):
        """Update state of control bar when configuration data is updated
        @param msg: ftpconfig.EDMSG_FTPCFG_UPDATED

        """
        # Refresh persistent state
        Profile_Set(CONFIG_KEY, ftpconfig.ConfigData.GetData())

        # Update view for new data
        self.RefreshControlBar()

    def OnDownload(self, evt):
        """File download has completed
        @param evt: ftpclient.EVT_FTP_DOWNLOAD

        """
        val = evt.GetValue()
        print "DOWNLOADED", val
        self._StartBusy(False)
        # TODO create proxy file and open in editor

    def OnItemActivated(self, evt):
        """Handle when items are activated in the list control
        @param evt: wx.EVT_LIST_ITEM_ACTIVATED

        """
        idx = evt.GetIndex()
        if idx < len(self._files):
            item = self._files[idx]
            path = item['name']
            if item['isdir']:
                # Change directory
                self._StartBusy(True)
                self._client.ChangeDirAsync(path)
            else:
                # Retrieve the file
                ed_msg.PostMessage(ed_msg.EDMSG_UI_SB_TXT,
                                   (ed_glob.SB_INFO,
                                   _("Retrieving file") + u"..."))
                self._StartBusy(True)
                self._client.DownloadAsync(path)

    def OnRefresh(self, evt):
        """Update the file list when a refresh event is sent by our
        ftp client.
        @param evt: ftpclient.EVT_FTP_REFRESH

        """
        if self._list.GetItemCount():
            self._list.DeleteAllItems()

        self._files = evt.GetValue()
        for item in self._files:
            self._list.AddItem(item)

        pid = self._mw.GetId()
        self._StartBusy(False)

    def OnThemeChanged(self, msg):
        """Update icons when the theme changes
        @param msg: ed_msg.EDMSG_THEME_CHANGED

        """
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_PREF), wx.ART_MENU)
        pref = self._cbar.FindWindowById(wx.ID_PREFERENCES)
        pref.SetBitmap(bmp)
        self._cbar.Layout()

    def RefreshControlBar(self):
        """Refresh the status of the control bar"""
        csel = self._sites.GetStringSelection()
        sites = self._config.GetSites()
        self._sites.SetItems(sites)
        if csel in sites:
            self._sites.SetStringSelection(csel)
        elif len(sites):
            self._sites.SetSelection(0)

        csel = self._sites.GetStringSelection()
        data = self._config.GetSiteData(csel)
        self._username.SetValue(self._config.GetSiteUsername(csel))
        self._password.SetValue(self._config.GetSitePassword(csel))
        self._cbar.Layout()
        self.EnableControls(len(sites))

#-----------------------------------------------------------------------------#

class FtpList(listmix.ListCtrlAutoWidthMixin,
               elistmix.ListRowHighlighter,
               wx.ListCtrl):
    """Ftp File List
    Displays the list of files in the currently connected ftp site.

    """
    def __init__(self, parent, id=wx.ID_ANY):
        wx.ListCtrl.__init__(self, parent, id, style=wx.LC_REPORT) 
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        elistmix.ListRowHighlighter.__init__(self)

        # Attributes
        self._il = wx.ImageList(16, 16)
        self._idx = dict()

        # Setup
        self.SetupImageList()
        self.InsertColumn(0, _("Filename"))
        self.InsertColumn(1, _("Size"))
        self.InsertColumn(2, _("Modified"))
        self.setResizeColumn(0)

        # Message Handlers
        ed_msg.Subscribe(self.OnThemeChanged, ed_msg.EDMSG_THEME_CHANGED)

    def __del__(self):
        """Unsubscribe from messages"""
        ed_msg.Unsubscribe(self.OnThemeChanged)

    def AddItem(self, item):
        """Add an item to the list
        @param item: dict(isdir, name, size, date)

        """
        self.Append((item['name'], item['size'], item['date']))
        if item['isdir']:
            img = self._idx['folder']
        else:
            img = self._idx['file']
        self.SetItemImage(self.GetItemCount() - 1, img)
        self.resizeLastColumn(self.GetTextExtent(u"Dec 31 24:00:00")[0] + 5)

    def OnThemeChanged(self, msg):
        """Update image list
        @param msg: ed_msg.EDMSG_THEME_CHANGED

        """
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_FOLDER), wx.ART_MENU)
        self._il.Replace(self._idx['folder'], bmp)

        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_FILE), wx.ART_MENU)
        self._il.Replace(self._idx['file'], bmp)

        self.Refresh()

    def SetupImageList(self):
        """Setup the image list"""
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_FOLDER), wx.ART_MENU)
        self._idx['folder'] = self._il.Add(bmp)

        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_FILE), wx.ART_MENU)
        self._idx['file'] = self._il.Add(bmp)

        self.SetImageList(self._il, wx.IMAGE_LIST_SMALL)
