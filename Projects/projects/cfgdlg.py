############################################################################
#    Copyright (C) 2007 Cody Precord                                       #
#    cprecord@editra.org                                                   #
#                                                                          #
#    Editra is free software; you can redistribute it and#or modify        #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    Editra is distributed in the hope that it will be useful,             #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

"""
#--------------------------------------------------------------------------#
# FILE: cfgdlg.py
# AUTHOR: Cody Precord
# LANGUAGE: Python
# SUMMARY:
#
#
# METHODS:
#
#
#
#--------------------------------------------------------------------------#
"""

__author__ = "Cody Precord <cprecord@editra.org>"
__cvsid__ = "$Id$"
__revision__ = "$Revision$"

#--------------------------------------------------------------------------#
# Dependancies
import wx

_ = wx.GetTranslation
#--------------------------------------------------------------------------#
# ConfigDlg Events
cfgEVT_CFG_EXIT = wx.NewEventType()
EVT_CFG_EXIT = wx.PyEventBinder(cfgEVT_CFG_EXIT, 1)
class ConfigDlgEvent(wx.PyCommandEvent):
    """Config dialog closer event"""
    def __init__(self, etype, eid, value=None):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._etype = etype
        self._id = eid
        self._value = value

    def GetEvtType(self):
        """Returns the event type
        @return: this events event type (ed_event)

        """
        return self._etype

    def GetId(self):
        """Returns the event id
        @return: the identifier of this event

        """
        return self._id

    def GetValue(self):
        """Returns the value from the event.
        @return: the value of this event

        """
        return self._value

#--------------------------------------------------------------------------#

class ConfigDlg(wx.MiniFrame):
    """Dialog for configuring the Projects plugin settings"""
    def __init__(self, parent, id, data, size=wx.DefaultSize):
        wx.MiniFrame.__init__(self, parent, id, _("Projects Configuration"), 
                              size=size, style=wx.DEFAULT_DIALOG_STYLE)

        # Attributes
        self._panel = ConfigPanel(self, data)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetInitialSize()
        self.CenterOnParent()

        # Event Handlers
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def GetConfigData(self):
        """Get the configuration data from the controls"""
        return self._panel.GetData()

    def OnClose(self, evt):
        """Catch the closure event and post the data to the dialogs
        parent.

        """
        wx.PostEvent(self.GetParent(), 
                     ConfigDlgEvent(cfgEVT_CFG_EXIT, self.GetId(), self.GetConfigData()))
        evt.Skip()

#--------------------------------------------------------------------------#

class ConfigPanel(wx.Panel):
    """Panel to hold controls for config dialog"""
    ID_CVS_PATH = wx.NewId()
    ID_DEFAULT_DIFF = wx.NewId()
    ID_DIFF_PATH = wx.NewId()
    ID_FILTERS = wx.NewId()
    ID_SVN_PATH = wx.NewId()
    ID_SYNC_NB = wx.NewId()
    def __init__(self, parent, data):
        wx.Panel.__init__(self, parent)
        
        # Attributes
        self._data = data

        # Layout
        self._DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnFileChange)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheck)

    def _DoLayout(self):
        """Build the panel with the controls"""
        sizer = wx.GridBagSizer(0, 20)
        sizer.Add((5, 5), (0, 0))

        # Source Control ctrls
        sbxsizer = wx.StaticBoxSizer(wx.StaticBox(self, label=_("Source Control")), wx.VERTICAL)
        cvssz = wx.BoxSizer(wx.HORIZONTAL)
        cvs = wx.StaticText(self, label="CVS: ")
        cpicker = wx.FilePickerCtrl(self, self.ID_CVS_PATH, self._data.GetCvsPath(),
                                    message=_("Select CVS Executable"))
        cvssz.AddMany([(cvs, 0, wx.ALIGN_CENTER_VERTICAL),
                       ((5, 5)), (cpicker, 1, wx.EXPAND)])
        svnsz = wx.BoxSizer(wx.HORIZONTAL)
        svn = wx.StaticText(self, label="SVN: ")
        spicker = wx.FilePickerCtrl(self, self.ID_SVN_PATH, self._data.GetSvnPath(),
                                    message=_("Select SVN Executable"))
        svnsz.AddMany([(svn, 0, wx.ALIGN_CENTER_VERTICAL),
                       ((5, 5)), (spicker, 1, wx.EXPAND)])
        sbxsizer.AddMany([(cvssz, 1, wx.EXPAND), (svnsz, 1, wx.EXPAND)])
        sizer.Add(sbxsizer, (1, 1), (2, 7), wx.EXPAND)

        # File Diff Controls
        dboxsz = wx.StaticBoxSizer(wx.StaticBox(self, label=_("Diff Program")), wx.VERTICAL)
        diffsz = wx.BoxSizer(wx.HORIZONTAL)
        difftxt = wx.StaticText(self, label="Diff: ")
        diff = self._data.GetDiffPath()
        differ = wx.FilePickerCtrl(self, self.ID_DIFF_PATH, diff,
                                   message=_("Select Diff Program"))
        diffcb = wx.CheckBox(self, self.ID_DEFAULT_DIFF, _("Use Builtin"))
        diffcb.SetValue(self._data.GetUseBuiltinDiff())
        differ.Enable(not diffcb.GetValue())
        diffsz.AddMany([(difftxt, 0, wx.ALIGN_CENTER_VERTICAL),
                        ((5, 5)), (differ, 1, wx.EXPAND)])
        dboxsz.AddMany([(diffcb, 0), (diffsz, 1, wx.EXPAND)])
        sizer.Add(dboxsz, (4, 1), (2, 7), wx.EXPAND)

        # File Filters
        fboxsz = wx.StaticBoxSizer(wx.StaticBox(self, label=_("File Filters")), wx.HORIZONTAL)
        filters = wx.TextCtrl(self, self.ID_FILTERS, 
                              value=self._data.GetFilters().replace(u':', u' '),
                              style=wx.TE_MULTILINE)
        tt = wx.ToolTip(_("Space separated list of files patterns to exclude from view"
                          "\nThe use of wildcards (*) are permitted."))
        filters.SetToolTip(tt)
        fboxsz.Add(filters, 1, wx.EXPAND)
        sizer.Add(fboxsz, (7, 1), (4, 7), wx.EXPAND)

        # Misc
        miscbsz = wx.StaticBoxSizer(wx.StaticBox(self, label=_("Miscellaneous")), wx.HORIZONTAL)
        nbsync = wx.CheckBox(self, self.ID_SYNC_NB, _("Syncronize with notebook"))
        nbsync.SetValue(self._data.GetSyncWithNotebook())
        miscbsz.Add(nbsync, 1, wx.EXPAND)
        sizer.Add(miscbsz, (12, 1), (1, 7), wx.EXPAND)

        sizer.AddMany([((5, 5), (13, 0)), ((5, 5), (13, 8))])
        self.SetSizer(sizer)
        self.SetInitialSize()

    def GetData(self):
        """Get the configuration data from the dialog"""
        for child in self.GetChildren():
            id = child.GetId()
            if id == self.ID_CVS_PATH:
                self._data.SetCvsPath(child.GetTextCtrl().GetValue())
            elif id == self.ID_SVN_PATH:
                self._data.SetSvnPath(child.GetTextCtrl().GetValue())
            elif id == self.ID_DEFAULT_DIFF:
                self._data.SetUseBuiltinDiff(child.GetValue())
            elif id == self.ID_DIFF_PATH:
                self._data.SetDiffPath(child.GetTextCtrl().GetValue())
            elif id == self.ID_FILTERS:
                self._data.SetFileFilters(child.GetValue())
            elif id == self.ID_SYNC_NB:
                self._data.SetSyncWithNotebook(child.GetValue())
            else:
                pass
        return self._data

    def OnCheck(self, evt):
        """Handle check box events"""
        e_id = evt.GetId()
        e_obj = evt.GetEventObject()
        if e_id == self.ID_DEFAULT_DIFF:
            val = e_obj.GetValue()
            differ = self.FindWindowById(self.ID_DIFF_PATH)
            if differ != None:
                differ.Enable(not val)
            self._data.SetUseBuiltinDiff(val)
        elif e_id == self.ID_SYNC_NB:
            self._data.SetSyncWithNotebook(e_obj.GetValue())
        else:
            evt.Skip()

    def OnFileChange(self, evt):
        """Handle events from the filepickers"""
        e_id = evt.GetId()
        path = evt.GetPath()
        if e_id == self.ID_CVS_PATH:
            self._data.SetCvsPath(path)
        elif e_id == self.ID_DIFF_PATH:
            self._data.SetDiffPath(path)
        elif e_id == self.ID_SVN_PATH:
            self._data.SetSvnPath(path)
        else:
            evt.Skip()

#--------------------------------------------------------------------------#

class ConfigData(dict):
    """Class for holding configuration data for the configdlg"""
    CVS = 'cvs'
    DIFF = 'diff'
    BUILTIN_DIFF = 'use_default_diff'
    FILTERS = 'filters'
    SVN = 'svn'
    SYNCNB = 'syncwithnotebook'
    def __init__(self, **kargs):
        dict.__init__(self)

        for key, val in kargs.iteritems():
            self.__setitem__(key, val)

    def GetCvsPath(self):
        """Get the path to cvs from the data"""
        return self.get(self.CVS, wx.EmptyString)

    def GetDiffPath(self):
        """Get the path to diff program"""
        return self.get(self.DIFF, wx.EmptyString)

    def GetFilters(self):
        """Get the file filters as a string of : separated values"""
        filters = self.get(self.FILTERS, wx.EmptyString)
        if filters != wx.EmptyString:
            filters = u':'.join(filters.split())
        return filters

    def GetSvnPath(self):
        """Get the path to svn from the data"""
        return self.get(self.SVN, wx.EmptyString)
        
    def GetSyncWithNotebook(self):
        return self.get(self.SYNCNB, True)

    def GetUseBuiltinDiff(self):
        return self.get(self.BUILTIN_DIFF, True)

    def SetCvsPath(self, path):
        """Set the path to cvs executable"""
        self.__setitem__(self.CVS, path)

    def SetDiffPath(self, path):
        """Set the path to diff program"""
        self.__setitem__(self.DIFF, path)

    def SetFileFilters(self, filters):
        """Set the file filters value
        @param filters: List of : separated filters

        """
        self.__setitem__(self.FILTERS, filters)

    def SetSvnPath(self, path):
        """Set the path to svn executable"""
        self.__setitem__(self.SVN, path)
        
    def SetSyncWithNotebook(self, sync):
        self.__setitem__(self.SYNCNB, sync)

    def SetUseBuiltinDiff(self, builtin):
        self.__setitem__(self.BUILTIN_DIFF, builtin)

#--------------------------------------------------------------------------#
# For testing

if __name__ == '__main__':
    app = wx.PySimpleApp(False)
    frame = wx.Frame(None, title="Configdlg Test Parent Frame")
    cfg = ConfigDlg(frame, wx.ID_ANY, ConfigData())
    frame.Show()
    cfg.Show()
    app.MainLoop()
