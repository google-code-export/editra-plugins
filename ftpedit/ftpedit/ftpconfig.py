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
import os
import wx

# Editra Libraries
import ed_glob
import ed_crypt

# Local Imports

#-----------------------------------------------------------------------------#
# Globals

_ = wx.GetTranslation
#-----------------------------------------------------------------------------#

class FtpConfigDialog(wx.Dialog):
    def __init__(self, parent, title=u''):
        wx.Dialog.__init__(self, parent, title=title)

        # Attributes
        self.config = ConfigData
        self._panel = FtpConfigPanel(self)

        # Layout
        self.__DoLayout()
        self.SetInitialSize()

        # Event Handlers
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnClose)

        wx.GetApp().RegisterWindow(repr(self), self)

    def __DoLayout(self):
        """Layout the Dialog"""
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self._panel, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def OnClose(self, evt):
        """Handle closing the dialog"""
        wx.GetApp().UnRegisterWindow(repr(self))
        evt.Skip()

#-----------------------------------------------------------------------------#

class FtpConfigPanel(wx.Panel):
    """Main Configuration Panel"""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Attributes
        self._sites = FtpSitesPanel(self)
        self._login = FtpLoginPanel(self)

        # Layout
        self.__DoLayout()

        # Event Handlers
        

    def __DoLayout(self):
        """Layout the Dialog"""
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Sites
        sizer.Add(self._sites, 0, wx.EXPAND)
        sizer.Add((10, 10), 0)

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(self._login, 0, wx.EXPAND)
        vsizer.Add((10, 10), 0)
        bsizer = wx.StdDialogButtonSizer()
        cancel = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
        save = wx.Button(self, wx.ID_SAVE, _("Save"))
        bsizer.AddButton(cancel)
        bsizer.AddButton(save)
        save.SetDefault()
        bsizer.Realize()
        vsizer.Add(bsizer, 0, wx.ALIGN_RIGHT)

        sizer.Add(vsizer, 0, wx.EXPAND)
        sizer.Add((10, 10), 0)

        # Final layout
        self.SetSizer(sizer)
        self.SetAutoLayout(True)

#-----------------------------------------------------------------------------#
# Left hand side panels
#-----------------------------------------------------------------------------#

class FtpSitesTree(wx.TreeCtrl):
    """Listing of saved sites"""
    def __init__(self, parent):
        """create the tree"""
        wx.TreeCtrl.__init__(self, parent,
                             style=wx.TR_DEFAULT_STYLE|\
                                   wx.TR_FULL_ROW_HIGHLIGHT|\
                                   wx.TR_EDIT_LABELS|\
                                   wx.TR_SINGLE|\
                                   wx.SIMPLE_BORDER)

        # Attributes
        self._editing = (None, None)
        self._imglst = wx.ImageList(16, 16)
        self._imgidx = dict(folder=0, site=1)
        self._root = None # TreeItemId

        # Setup
        self.SetImageList(self._imglst)
        self.__SetupImageList()
        self._root = self.AddRoot(_("My Sites"), self._imgidx['folder'])
        self.SetItemHasChildren(self._root, True)
        self.Expand(self._root)
        self.SetMinSize(wx.Size(-1, 150))

        # Event Handlers
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginLabelEdit)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndLabelEdit)

    def __SetupImageList(self):
        """Setup the image list"""
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_FOLDER), wx.ART_MENU)
        self._imgidx['folder'] = self._imglst.Add(bmp)

        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_WEB), wx.ART_MENU)
        self._imgidx['site'] = self._imglst.Add(bmp)

    def CanRemove(self):
        """Can the selected item be removed
        @return: bool

        """
        return self.GetSelection() != self._root

    def NewSite(self, name):
        """Add a new site node
        @param name: site name

        """
        item = self.AppendItem(self._root, name, self._imgidx['site'])
        self.SetItemPyData(item, dict(url=u'', port=u'21', user=u'', pword=u''))
        wx.CallAfter(self.SortChildren, self._root)
        if not self.IsExpanded(self._root):
            self.Expand(self._root)

    def OnBeginLabelEdit(self, evt):
        """Handle updating after a tree label has been edited"""
        item = evt.GetItem()
        if item != self._root:
            self._editing = (item, self.GetItemText(item))
            evt.Skip()
        else:
            # Don't allow root to be edited
            evt.Veto()

    def OnEndLabelEdit(self, evt):
        """Handle updating after a tree label has been edited"""
        item = evt.GetItem()
        if item != self._root and item == self._editing[0]:
            label = self.GetItemText(item)
            old = self._editing[1]
            self._editing = (None, None)
            if old != label:
                # TODO: UPDATE CONFIG
                print label
        else:
            evt.Skip()

    def RemoveSelected(self):
        """Remove the selected site"""
        sel = self.GetSelection()
        if sel != self._root:
            self.Delete(sel)
            # TODO: Remove from config as well
        else:
            pass

#-----------------------------------------------------------------------------#

class FtpSitesPanel(wx.Panel):
    """Sites Panel"""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Attributes
        self._box = wx.StaticBox(self, label=_("Sites:"))
        self._tree = FtpSitesTree(self)

        # Layout
        self.__DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeSelChanged)
        self.Bind(wx.EVT_BUTTON, self.OnButton)

    def __DoLayout(self):
        """Layout the Dialog"""
        sizer = wx.BoxSizer(wx.VERTICAL)

        boxsz = wx.StaticBoxSizer(self._box, wx.VERTICAL)
        sizer.Add(self._tree, 1, wx.EXPAND|wx.ALIGN_LEFT)

        # Buttons
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        newbtn = wx.Button(self, wx.ID_NEW, _("New Site"))
        delbtn = wx.Button(self, wx.ID_DELETE, _("Delete"))
        if wx.Platform == '__WXMAC__':
            newbtn.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)
            delbtn.SetWindowVariant(wx.WINDOW_VARIANT_SMALL) 
        delbtn.Enable(False)
        hsizer.AddMany([(newbtn, 0, wx.ALIGN_CENTER_VERTICAL),
                        ((5, 5), 0),
                        (delbtn, 0, wx.ALIGN_CENTER_VERTICAL)])

        sizer.AddMany([((5, 5), 0), (hsizer, 0, wx.EXPAND)])
        boxsz.Add(sizer, 0, wx.EXPAND)

        msizer = wx.BoxSizer(wx.HORIZONTAL)
        msizer.AddMany([((5, 5), 0), (boxsz, 0), ((5, 5), 0)])
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.AddMany([((5, 5), 0), (msizer, 0, wx.EXPAND), ((5, 5), 0)])
        self.SetSizer(vsizer)
        self.SetAutoLayout(True)

    def OnButton(self, evt):
        """Handle Button clicks"""
        e_id = evt.GetId()
        if e_id == wx.ID_NEW:
            # TODO: make sure its unique name and update config with
            #       empty configuration.
            item = self._tree.NewSite(_("New Site"))
        elif e_id == wx.ID_DELETE:
            item = self._tree.GetSelection()
            self._tree.Delete(item)
            #TODO: delete from config
        else:
            evt.Skip()

    def OnTreeSelChanged(self, evt):
        """Notify parent of change in tree"""
        item = evt.GetItem()
        self.FindWindowById(wx.ID_DELETE).Enable(item != self._tree.GetRootItem())

        old = evt.GetOldItem()
        # TODO: Store old selection
        print self._tree.GetItemText(item)

#-----------------------------------------------------------------------------#
# Right hand side panels
#-----------------------------------------------------------------------------#

class FtpLoginPanel(wx.Panel):
    """Login information panel"""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Attributes
        self._box = wx.StaticBox(self, label=_("Login Settings"))
        self._boxsz = wx.StaticBoxSizer(self._box, wx.HORIZONTAL)
        self._host = wx.TextCtrl(self)
        self._port = wx.TextCtrl(self, value=u"21")
        self._user = wx.TextCtrl(self)
        self._pass = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        self._path = wx.TextCtrl(self)

        # Layout
        self.__DoLayout()
        self.SetInitialSize()

        # Event handlers
        

    def __DoLayout(self):
        """Layout the panel"""
        sizer = wx.BoxSizer(wx.VERTICAL)

        host_sz = wx.BoxSizer(wx.HORIZONTAL)
        host_sz.AddMany([(self._host, 1, wx.EXPAND), ((5, 5)),
                         (wx.StaticText(self, label=_("Port:")), 0, wx.ALIGN_CENTER_VERTICAL),
                         ((5, 5)), (self._port, 0, wx.ALIGN_CENTER_VERTICAL)])

        fgrid = wx.FlexGridSizer(6, 2, 10, 5)
        fgrid.AddGrowableCol(1, 1)
        fgrid.AddMany([(wx.StaticText(self, label=_("Host:")), 0, wx.ALIGN_CENTER_VERTICAL),
                       (host_sz, 1, wx.EXPAND),

                       (wx.StaticLine(self, size=(-1, 2), style=wx.LI_HORIZONTAL), 0, wx.EXPAND),
                       (wx.StaticLine(self, size=(-1, 2), style=wx.LI_HORIZONTAL), 0, wx.EXPAND),

                       (wx.StaticText(self, label=_("User:")), 0, wx.ALIGN_CENTER_VERTICAL),
                       (self._user, 0, wx.EXPAND),
                       
                       (wx.StaticText(self, label=_("Password:")), 0, wx.ALIGN_CENTER_VERTICAL),
                       (self._pass, 0, wx.EXPAND),

                       (wx.StaticLine(self, size=(-1, 2), style=wx.LI_HORIZONTAL), 0, wx.EXPAND),
                       (wx.StaticLine(self, size=(-1, 2), style=wx.LI_HORIZONTAL), 0, wx.EXPAND),

                       (wx.StaticText(self, label=_("Default Path:")), 0, wx.ALIGN_CENTER_VERTICAL),
                       (self._path, 0, wx.EXPAND)
                       ])

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddMany([((5, 5), 0), (fgrid, 1, wx.EXPAND), ((5, 5), 0)])
        
        self._boxsz.Add(hsizer, 1, wx.EXPAND)
        sizer.AddMany([((5, 5), 0), (self._boxsz, 0, wx.EXPAND), ((5, 5), 0)])

        if wx.Platform == '__WXMAC__':
            for child in self.GetChildren():
                if not isinstance(child, wx.StaticLine):
                    child.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)

    def GetLoginInfo(self):
        """Get the login information
        @return: {url:'',port:'',user:'',pword:''}
        @rtype: dict

        """
        rdict = dict(url=self._host.GetValue(),
                     port=self._port.GetValue(),
                     user=self._user.GetValue(),
                     pword=self._pass.GetValue())
        return rdict

    def SetHostName(self, name):
        """Set the hostname field
        @param name: string

        """
        self._host.SetValue(name)

    def SetPort(self, port):
        """Set the port field
        @param port: string

        """
        self._port.SetValue(port)

    def SetUserName(self, name):
        """Set the username field
        @param name: string

        """
        self._user.SetValue(name)

    def SetPassword(self, pword):
        """Set the hostname field
        @param pword: string

        """
        self._pword.SetValue(name)

#-----------------------------------------------------------------------------#

class __ConfigData(object):
    """Configuration data Object"""
    DEFAULT = dict(url=u'', port=u'21', user=u'', pword=u'')
    def __init__(self, data):
        """Create a configration data object
        @param data: dict

        """
        object.__init__(self)

        # Attributes
        self._data = data

    def AddSite(self, name, url=u'', port=u'', user=u'', pword=u''):
        """Add/Update a site in the configuration
        @param name: configuration name
        @keyword url: site url
        @keyword port: port number
        @keyword user: username
        @keyword pword: password

        """
        data = dict(url=url, port=port, user=user, pword=pword)
        salt = os.urandom(8)
        pword = ed_crypt.Encrypt(data['pword'], salt)
        data['salt'] = salt
        data['pword'] = pword
        self._data[name] = data

    def GetCount(self):
        """Get number of sites in the config
        @return: int

        """
        return len(self._data.keys())

    def GetSite(self, name):
        """Get the information for a given site
        @param name: site name

        """
        data = self._data.get(name, None)
        if data is None:
            return dict(ConfigData.DEFAULT)

        pword = ed_crypt.Decrypt(data['pword'], data['salt'])
        rdata = dict(data)
        del rdata['salt']
        rdata['pword'] = pword
        return rdata

    def SetData(self, data):
        """Set the configurations site data
        @param data: dict(name=dict(url,port,user,pword))

        """
        self._data = data

#-----------------------------------------------------------------------------#

ConfigData = __ConfigData(dict())

