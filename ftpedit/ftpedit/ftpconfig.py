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
import ed_msg
from eclib.encdlg import GetAllEncodings

# Local Imports

#-----------------------------------------------------------------------------#
# Globals
EDMSG_FTPCFG_UPDATED = ('FtpEdit', 'cfg', 'updated')
EDMSG_FTPCFG_LOADED = ('FtpEdit', 'cfg', 'loaded')

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
        self._login.Disable()

        # Layout
        self.__DoLayout()

        # Setup
        self._sites.SetSelectionNotifier(self.OnSelectionNotify)

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wx.ID_SAVE)
        self.Bind(wx.EVT_BUTTON, self.GetParent().OnClose, id=wx.ID_CANCEL)

    def __DoLayout(self):
        """Layout the Dialog"""
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Sites
        vsizer2 = wx.BoxSizer(wx.VERTICAL)
        vsizer2.Add(self._sites, 1, wx.EXPAND)
        sizer.Add(vsizer2, 1, wx.EXPAND)
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
        vsizer.Add((5, 5), 0)

        sizer.Add(vsizer, 0, wx.EXPAND)
        sizer.Add((10, 10), 0)

        # Final layout
        self.SetSizer(sizer)
        self.SetAutoLayout(True)

    def OnSave(self, evt):
        """Save the configuration"""
        evt.Skip()

    def OnSelectionNotify(self, old, new, isroot):
        """Notification callback for when tree selection changes
        @param old: old label string
        @param new: new item string
        @param isroot: old selection was root item (bool)

        """
        if not isroot:
            info = self._login.GetLoginInfo()
            ConfigData.AddSite(old, **info)

        self._login.Enable(isroot)
        ninfo = ConfigData.GetSiteData(new)
        self._login.SetLoginInfo(ninfo)

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
        for site in ConfigData.GetSites():
            self.AppendItem(self._root, site, self._imgidx['site'])
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

    def GetNodeLabels(self):
        """Get the labels of all the nodes
        @return: list of strings

        """
        count = self.GetChildrenCount(self._root)
        nodes = list()
        if count:
            child = self.GetFirstChild(self._root)
            lchild = self.GetLastChild(self._root)
            while child != lchild:
                txt = self.GetItemText(child)
                nodes.append(txt)
                child = self.GetNextSibling(child)
            nodes.append(self.GetItemText(lchild))

        return nodes

    def NewSite(self, name):
        """Add a new site node
        @param name: site name

        """
        item = self.AppendItem(self._root, name, self._imgidx['site'])
        wx.CallLater(200, self.EditLabel, item)
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
                wx.CallAfter(self.SortChildren, self._root)
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
        self._box = wx.StaticBox(self, label=_("Sites"))
        self._tree = FtpSitesTree(self)
        self._selNotifier = None

        # Layout
        self.__DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeSelChanged)
        self.Bind(wx.EVT_BUTTON, self.OnButton)

    def __DoLayout(self):
        """Layout the Dialog"""
        sizer = wx.BoxSizer(wx.VERTICAL)

        boxsz = wx.StaticBoxSizer(self._box, wx.VERTICAL)
        sizer.Add(self._tree, 1, wx.EXPAND)

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
        boxsz.Add(sizer, 1, wx.EXPAND)

        msizer = wx.BoxSizer(wx.HORIZONTAL)
        msizer.AddMany([((5, 5), 0), (boxsz, 1, wx.EXPAND), ((5, 5), 0)])
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.AddMany([((5, 5), 0), (msizer, 1, wx.EXPAND), ((5, 5), 0)])
        self.SetSizer(vsizer)
        self.SetAutoLayout(True)

    def GetTreeCtrl(self):
        """Get this panels tree control
        @return: FtpSitesTree

        """
        return self._tree

    def OnButton(self, evt):
        """Handle Button clicks"""
        e_id = evt.GetId()
        if e_id == wx.ID_NEW:
            # TODO: make sure its unique name and update config with
            #       empty configuration.
            item = self._tree.NewSite(_("New Site"))
        elif e_id == wx.ID_DELETE:
            item = self._tree.GetSelection()
            site = self._tree.GetItemText(item)

            # Delete from Config and tree view
            self._tree.Delete(item)
            ConfigData.RemoveSite(site)
        else:
            evt.Skip()

    def OnTreeSelChanged(self, evt):
        """Notify parent of change in tree"""
        item = evt.GetItem()
        self.FindWindowById(wx.ID_DELETE).Enable(item != self._tree.GetRootItem())

        old = evt.GetOldItem()
        if self._selNotifier is not None:
            oldlbl = u''
            newlbl = u''
            if old.IsOk():
                oldlbl = self._tree.GetItemText(old)

            if item.IsOk():
                newlbl = self._tree.GetItemText(item)

            self._selNotifier(oldlbl,
                              newlbl,
                              old == self._tree.GetRootItem())

    def SetSelectionNotifier(self, callb):
        """Set the selction changed notifier method
        @param callb: def fun(old_sel, new_sel, isroot)

        """
        self._selNotifier = callb

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
        self._enc = wx.Choice(self, choices=GetAllEncodings())

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

        fgrid = wx.FlexGridSizer(7, 2, 10, 5)
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
                       (self._path, 0, wx.EXPAND),

                       (wx.StaticText(self, label=_("Encoding:")), 0, wx.ALIGN_CENTER_VERTICAL),
                       (self._enc, 0, wx.EXPAND)
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
                     pword=self._pass.GetValue(),
                     path=self._path.GetValue(),
                     enc=self._enc.GetStringSelection())
        return rdict

    def SetLoginInfo(self, info):
        """Set the data in all the fields
        @param info: login info dict

        """
        vmap = { 'url' : self.SetHostName,
                 'port' : self.SetPort,
                 'user' : self.SetUserName,
                 'pword' : self.SetPassword,
                 'path' : self.SetDefaultPath,
                 'enc' : self.SetEncoding }

        for key, val in info.iteritems():
            vmap.get(key, lambda v: len(v))(val)

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
        self._pass.SetValue(pword)

    def SetDefaultPath(self, path):
        """Set the default path field
        @param path: string

        """
        self._path.SetValue(path)

    def SetEncoding(self, enc):
        """Set the encoding to use
        @param enc: string

        """
        self._enc.SetStringSelection(enc)

#-----------------------------------------------------------------------------#

class __ConfigData(object):
    """Configuration Data Object"""
    DEFAULT = dict(url=u'', port=u'21', user=u'',
                   pword=u'', path=u'', enc=u'utf-8')
    def __init__(self, data):
        """Create a configration data object
        @param data: dict

        """
        object.__init__(self)

        # Attributes
        self._data = data

    def AddSite(self, name, url=u'', port=u'21', user=u'',
                      pword=u'', path=u'', enc=u'utf-8'):
        """Add/Update a site in the configuration
        @param name: configuration name
        @keyword url: site url
        @keyword port: port number
        @keyword user: username
        @keyword pword: password
        @keyword path: default path
        @keyword enc: encoding

        """
        data = dict(url=url, port=port, user=user,
                    pword=pword, path=path, enc=enc)
        salt = os.urandom(8)
        pword = ed_crypt.Encrypt(data['pword'], salt)
        data['salt'] = salt
        data['pword'] = pword
        self._data[name] = data

        # Notify all others of change
        ed_msg.PostMessage(EDMSG_FTPCFG_UPDATED, (name,))

    def GetCount(self):
        """Get number of sites in the config
        @return: int

        """
        return len(self._data.keys())

    def GetData(self):
        """Get the configuration data dictionary
        @return: dict

        """
        return self._data

    def GetSiteData(self, name):
        """Get the information for a given site
        @param name: site name
        @return: site config dictionary

        """
        data = self._data.get(name, None)
        if data is None:
            return dict(ConfigData.DEFAULT)

        pword = ed_crypt.Decrypt(data['pword'], data['salt'])
        rdata = dict(data)
        del rdata['salt']
        rdata['pword'] = pword
        return rdata

    def GetSites(self):
        """Return the list of configured sites
        @return: list of strings

        """
        return sorted(self._data.keys())

    def GetSitePassword(self, site):
        """Get the password set for the given site
        @return: string

        """
        data = self.GetSiteData(site)
        return data['pword']

    def GetSiteUsername(self, site):
        """Get the username configured for the given site
        @param site: site name
        @return: string

        """
        data = self.GetSiteData(site)
        return data['user']

    def RemoveSite(self, site):
        """Remove a site from the config
        @param site: site name

        """
        if site in self._data:
            del self._data[site]
        
    def SetData(self, data):
        """Set the configurations site data
        @param data: dict(name=dict(url,port,user,pword,path,enc))

        """
        self._data = data

        # Notify of settings load
        ed_msg.PostMessage(EDMSG_FTPCFG_LOADED)

#-----------------------------------------------------------------------------#

ConfigData = __ConfigData(dict())

