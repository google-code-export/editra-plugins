###############################################################################
# Name: ptcfg.py                                                              #
# Purpose: PyTools Configuration                                              #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2009 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

__author__ = "Cody Precord <cprecord@editra.org> "
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#--------------------------------------------------------------------------#
# Dependancies
import cStringIO
import zlib
import wx
import wx.lib.mixins.listctrl as listmix

# Editra Libraries
#import sys
#sys.path.insert(0, 'C:\\Documents and Settings\\cjprecord\\Desktop\\Editra\\src')
import eclib

#-----------------------------------------------------------------------------#
# Globals
ID_INSTALLATIONS = wx.NewId()
ID_BROWSE = wx.NewId()

_ = wx.GetTranslation

#-----------------------------------------------------------------------------#
# TODO: Add these as resources in editra's artprovider as they are used in
#       multiple locations.

def GetMinusData():
    return zlib.decompress(
"x\xda\xeb\x0c\xf0s\xe7\xe5\x92\xe2b``\xe0\xf5\xf4p\t\x02\xd2< \xcc\xc1\x06$\
\xc3Jc\x9e\x03)\x96b'\xcf\x10\x0e \xa8\xe1H\xe9\x00\xf2\x9d<]\x1cC4&&\xa7\
\xa4$\xa5)\xb0\x1aL\\RU\x90\x95\xe0\xf8,\xc6\xaa\xf0\xcf\xffr\x13\xd69\x87\
\xb8x\xaaVM\xea\x890\xf512N\x9e\xb1v\xf5\xe9\x05\xdc\xc2;jf:\x96\xdf\xd2\x14\
a\x96pO\xda\xc0\xc4\xa0\xf4\x8a\xab\xcau\xe2|\x1d\xa0i\x0c\x9e\xae~.\xeb\x9c\
\x12\x9a\x00Ij($" )

def GetMinusBitmap():
    stream = cStringIO.StringIO(GetMinusData())
    return wx.BitmapFromImage(wx.ImageFromStream(stream))

#----------------------------------------------------------------------

def GetPlusData():
    return zlib.decompress(
"x\xda\xeb\x0c\xf0s\xe7\xe5\x92\xe2b``\xe0\xf5\xf4p\t\x02\xd2< \xcc\xc1\x06$\
\xc3Jc\x9e\x03)\x96b'\xcf\x10\x0e \xa8\xe1H\xe9\x00\xf2{<]\x1cC4&&'Hp\x1c\
\xd8\xb9\xcf\xe6U\xfd\xefi\xbb\xffo\xf44J\x14L\xae\xde\x97+yx\xd3\xe9\xfc\
\x8d\xb3\xda|\x99\x99g\x1b07\x1b\xd8k\x87\xf1\xea\x18\x1c{\xaa\xec\xfe\xaf>%\
!\xf9A\xda\xef\x03\x06\xf67{\x1f\x1e\xf8\xf9\x98g\xf9\xb9\xf9\xbf\xfe\xbf~\
\xad\xcf\x96'h\xca\xe6\xcck\xe8&2\xb7\x8e\x87\xe7\xbfdAB\xfb\xbf\xe0\x88\xbf\
\xcc\xcc\x7f.\xcbH\xfc{\xfd(\xa0\xe5*\xff\xfd\xff\x06\x06\x1f\xfe\xffh\xbaj\
\xf2f^ZB\xc2\x83\xe4\xc3\xef2o13<r\xd5y\xc0\xb9\xc2\xfa\x0e\xd0]\x0c\x9e\xae\
~.\xeb\x9c\x12\x9a\x00\xcf9S\xc6" )

def GetPlusBitmap():
    stream = cStringIO.StringIO(GetPlusData())
    return wx.BitmapFromImage(wx.ImageFromStream(stream))

#--------------------------------------------------------------------------#

class PyToolsCfgPanel(wx.Panel):
    """Configuration panel to be displayed in the PluginManager."""
    def __init__(self, parent):
        """Initialize the panel
        @param parent: PluginMgrDlg Notebook

        """
        wx.Panel.__init__(self, parent)

        # Attributes
        
        # Layout
        self.__DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnButton)

    def __DoLayout(self):
        """Layout the panel"""
        msizer = wx.BoxSizer(wx.VERTICAL)

        # Main area
        sbox = wx.StaticBox(self, label=_("Python Installations"))
        boxsz = wx.StaticBoxSizer(sbox, wx.VERTICAL)

        # Default exe
        dsizer = wx.BoxSizer(wx.HORIZONTAL)
        def_ch = wx.Choice(self, wx.ID_DEFAULT, choices=["Python",])
        def_ch.SetSelection(0)
        dsizer.AddMany([(wx.StaticText(self, label=_("Default") + ":"), 0,
                         wx.ALIGN_CENTER_VERTICAL), ((5, 5), 0),
                        (def_ch, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)])

        # Executables List
        exelist = CommandListCtrl(self, ID_INSTALLATIONS,
                                  style=wx.LC_EDIT_LABELS|\
                                        wx.BORDER|wx.LC_REPORT|\
                                        wx.LC_SINGLE_SEL)
        # TODO: populate list from persisted configuration

        addbtn = wx.BitmapButton(self, wx.ID_ADD, GetPlusBitmap())
        addbtn.SetToolTipString(_("Add a new python installation"))
        delbtn = wx.BitmapButton(self, wx.ID_REMOVE, GetMinusBitmap())
        delbtn.SetToolTipString(_("Remove selection from list"))
        btnsz = wx.BoxSizer(wx.HORIZONTAL)
        btnsz.AddMany([(addbtn, 0), ((2, 2), 0), (delbtn, 0)])

        # Box Sizer Layout
        boxsz.AddMany([((5, 5), 0), (dsizer, 0, wx.ALIGN_CENTER|wx.EXPAND),
                       ((5, 5), 0), (wx.StaticLine(self), 0, wx.EXPAND),
                       ((8, 8), 0), (exelist, 1, wx.EXPAND), ((5, 5), 0),
                       (btnsz, 0, wx.ALIGN_LEFT)])

        # Setup the main sizer
        msizer.AddMany([((10, 10), 0),
                        (boxsz, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
                        ((10, 10), 0)])

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddMany([((8, 8), 0), (msizer, 1, wx.EXPAND), ((8, 8), 0)])
        self.SetSizer(hsizer)
        self.SetAutoLayout(True)

    def OnButton(self, evt):
        """Handle the add and remove button events
        @param evt: wxButtonEvent

        """
        e_id = evt.GetId()
        elist = self.FindWindowById(ID_INSTALLATIONS)
        if e_id == wx.ID_ADD:
            elist.Append([_("**Alias**"), _("**New Value**")])
        elif e_id == wx.ID_REMOVE:
            item = -1
            items = []
            while True:
                item = elist.GetNextItem(item, wx.LIST_NEXT_ALL,
                                         wx.LIST_STATE_SELECTED)
                if item == -1:
                    break
                items.append(item)

            for item in reversed(sorted(items)):
                elist.DeleteItem(item)

        else:
            evt.Skip()

#-----------------------------------------------------------------------------#

class CommandListCtrl(listmix.ListCtrlAutoWidthMixin,
                        listmix.TextEditMixin,
                        eclib.ListRowHighlighter,
                        wx.ListCtrl):
    """Auto-width adjusting list for showing editing the commands"""
    def __init__(self, *args, **kwargs):
        wx.ListCtrl.__init__(self, *args, **kwargs)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        eclib.ListRowHighlighter.__init__(self)

        # Attributes
        self._menu = None
        self._cindex = -1

        # Setup
        self.SetToolTipString(_("Click on an item to edit"))
        self.InsertColumn(0, _("Alias"))
        self.InsertColumn(1, _("Installation Path"))

        listmix.TextEditMixin.__init__(self)

        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnContextClick)
        self.Bind(wx.EVT_MENU, self.OnMenu, id=ID_BROWSE)

    def OnContextClick(self, evt):
        """Handle right clicks"""
        if not self.GetSelectedItemCount():
            evt.Skip()
            return

        if self._menu is None:
            # Lazy init of menu
            self._menu = wx.Menu()
            self._menu.Append(ID_BROWSE, _("Browse"))

        self._cindex = evt.GetIndex()
        self.PopupMenu(self._menu)

    def OnMenu(self, evt):
        """Handle Menu events"""
        e_id = evt.GetId()
        if e_id == ID_BROWSE:
            dlg = wx.FileDialog(self, _("Choose and executable"))
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                if self._cindex >= 0:
                    self.SetStringItem(self._cindex, 1, path)
                    levt = wx.ListEvent(wx.wxEVT_COMMAND_LIST_END_LABEL_EDIT,
                                        self.GetId())
# TODO: ERR ><! there are no setters for index, column, and label...
#                    levt.Index = self._cindex
#                    levt.SetInt(self._cindex)
#                    levt.Column = 1
#                    levt.Label = path
                    # HACK set the member variables directly...
                    levt.m_itemIndex = self._cindex
                    levt.m_col = 1
                    levt.SetString(path)
                    wx.PostEvent(self.GetParent(), levt)
        else:
            evt.Skip()

#-----------------------------------------------------------------------------#
# Test

if __name__ == '__main__':
    app = wx.App(False)
    frame = wx.Frame(None, title="Pytools Config")
    panel = PyToolsCfgPanel(frame)
    frame.Show()
    app.MainLoop()
