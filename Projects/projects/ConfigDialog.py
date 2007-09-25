#!/usr/bin/env python

import wx, sys
import wx.lib.mixins.listctrl as listmix

_ = wx.GetTranslation

# ConfigDialogg Events
cfgEVT_CONFIG_EXIT = wx.NewEventType()
EVT_CONFIGG_EXIT = wx.PyEventBinder(cfgEVT_CONFIG_EXIT, 1)

class ConfigDialogEvent(wx.PyCommandEvent):
    """ Config dialog closer event """
    def __init__(self, etype, eid, value=None):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._etype = etype
        self._id = eid
        self._value = value

    def GetId(self):
        """ Returns the event id """
        return self._id

    def GetValue(self):
        """ Returns the value from the event """
        return self._value
        

class ConfigDialog(wx.MiniFrame):
    """Dialog for configuring the Projects plugin settings"""
    def __init__(self, parent, id, data, size=wx.DefaultSize):
        wx.MiniFrame.__init__(self, parent, id, _("Projects Configuration"), 
                              size=size, style=wx.DEFAULT_DIALOG_STYLE)

        # Attributes
        self._notebook = ConfigNotebook(self, -1, data)
        self._data = data

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.Panel(self, -1, size=(1,5)))
        sizer.AddF(self._notebook, wx.SizerFlags().Expand().Border(wx.LEFT|wx.RIGHT|wx.BOTTOM, 20))

        self.SetSizer(sizer)
        self.SetInitialSize()
        self.CenterOnParent()

        # Event Handlers
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        """ Notify watchers that the config data has changed """
        wx.PostEvent(self.GetParent(), 
                     ConfigDialogEvent(cfgEVT_CONFIG_EXIT, self.GetId(), self._data))
        evt.Skip()

class ConfigNotebook(wx.Notebook):
    def __init__(self, parent, id, data):
        wx.Notebook.__init__(self, parent, id, size=(450,-1), style=
                             wx.BK_DEFAULT
                             #wx.BK_TOP 
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                             # | wx.NB_MULTILINE
                             )

        self.AddPage(GeneralConfigTab(self, -1, data), _("General"))
        self.AddPage(SourceControlConfigTab(self, -1, data), _("Source Control"))

class GeneralConfigTab(wx.Panel):
    def __init__(self, parent, id, data):
        wx.Panel.__init__(self, parent, id)
        self._data = data
        
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        flags = wx.SizerFlags().Left().Expand().Border(wx.ALL, 6)
        sizer.AddF(wx.StaticText(self, -1, _('File Filters')), flags)
        sizer.AddF(wx.TextCtrl(self, -1, data['general'].get('file-filters',''), size=(-1, 100)), flags)
        sizer.AddF(wx.StaticBox(self, -1, size=(-1, 1)), wx.SizerFlags().Center().Expand().Border(wx.TOP|wx.BOTTOM, 10))
        sizer.AddF(wx.CheckBox(self, -1, _('Keep project tree synchronized with editor notebook')), flags)
        sizer.AddF(wx.StaticBox(self, -1, size=(-1, 1)), wx.SizerFlags().Center().Expand().Border(wx.TOP|wx.BOTTOM, 10))
        sizer.AddF(wx.StaticText(self, -1, _('Diff Program')), flags)
        sizer.AddF(wx.RadioButton(self, -1, _('Built-in')), flags.Border(wx.TOP|wx.LEFT, 6))
        
        # Radio button with file selector
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddF(wx.RadioButton(self, -1, ''), wx.SizerFlags().Left().Border(wx.TOP|wx.BOTTOM|wx.LEFT, 6))
        hsizer.AddF(wx.FilePickerCtrl(self, -1, data['general'].get('diff-program',''),
                                      message=_("Select diff program")), wx.SizerFlags(1).Left().Expand())
        sizer.AddF(hsizer, wx.SizerFlags().Left().Expand())
        
        # Extra space at bottom of panel
        sizer.AddF(wx.Panel(self, -1), wx.SizerFlags().Border(wx.TOP, 10))

        # Add space around the sides
        outsizer = wx.BoxSizer(wx.HORIZONTAL)
        outsizer.AddF(wx.Panel(self, -1, size=(10,5)), wx.SizerFlags(0))
        outsizer.AddF(sizer, wx.SizerFlags(1).Expand())
        outsizer.AddF(wx.Panel(self, -1, size=(10,5)), wx.SizerFlags(0))
        
        self.SetSizer(outsizer)
        self.SetInitialSize()
        
class SourceControlConfigTab(wx.Panel):
    def __init__(self, parent, id, data):
        wx.Panel.__init__(self, parent, id)
        self._data = data
        
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        flags = wx.SizerFlags().Left().Border(wx.ALL, 6)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddF(wx.Choice(self, -1, choices=['CVS','Git','Subversion']), flags.Border(wx.ALL,5))
        hsizer.AddF(wx.FilePickerCtrl(self, -1), wx.SizerFlags(1))        
        sizer.AddF(hsizer, wx.SizerFlags(1).Expand())
        
        # Repository configuration box
        repsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, _('Repository Configuration')), wx.VERTICAL)

        # Repository selector
        repsizer.AddF(wx.Choice(self, -1, choices=['Default','','Add Repository...','Remove Repository...']), flags.Expand())
        
        # Username and password
        userpass = wx.FlexGridSizer(2,2)
        userpass.AddGrowableCol(1,1)
        userpass.AddF(wx.StaticText(self, -1, _('Username')), flags)
        userpass.AddF(wx.TextCtrl(self, -1), flags)
        userpass.AddF(wx.StaticText(self, -1, _('Password')), flags)
        userpass.AddF(wx.TextCtrl(self, -1), flags)
        repsizer.AddF(userpass, wx.SizerFlags(1).Expand())
        repsizer.AddF(wx.StaticBox(self, -1, size=(-1, 1)), wx.SizerFlags().Center().Expand().Border(wx.TOP|wx.BOTTOM, 10))

        # Environment variables
        repsizer.AddF(wx.StaticText(self, -1, _('Environment Variables')), flags)
        env = AutoWidthListCtrl(self, -1, size=(-1,60), style=wx.LC_REPORT|wx.LC_SORT_ASCENDING|wx.LC_VRULES|wx.LC_EDIT_LABELS)
        env.InsertColumn(0, _("Name"))
        env.InsertColumn(1, _("Value"))
        index = env.InsertStringItem(sys.maxint, '')
        env.SetStringItem(index, 0, 'NEW_VAR')
        env.SetStringItem(index, 1, 'NEW VAR VALUE')
        repsizer.AddF(env, flags.Expand())

        sizer.AddF(repsizer, flags)

        # Extra space at bottom of panel
        sizer.AddF(wx.Panel(self, -1), wx.SizerFlags().Border(wx.TOP, 10))

        # Add space around the sides
        outsizer = wx.BoxSizer(wx.HORIZONTAL)
        outsizer.AddF(wx.Panel(self, -1, size=(10,5)), wx.SizerFlags(0))
        outsizer.AddF(sizer, wx.SizerFlags(1).Expand())
        outsizer.AddF(wx.Panel(self, -1, size=(10,5)), wx.SizerFlags(0))

        self.SetSizer(outsizer)
        self.SetInitialSize()
        
class AutoWidthListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, *args, **kwargs):
        wx.ListCtrl.__init__(self, *args, **kwargs)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

class ConfigData(dict):
    configKeys = ['general','source-control']
    def __init__(self, data={}):
        self.update(data)
        for key in self.configKeys:
            if key not in self:
                self[key] = {}

if __name__ == '__main__':
    app = wx.PySimpleApp(False)
    frame = wx.Frame(None, title="Config Dialog Parent Frame", size=(480, 335))
    cfg = ConfigDialog(frame, wx.ID_ANY, ConfigData())
    #cfg = GeneralConfigTab(frame, -1, ConfigData())
    #cfg = SourceControlConfigTab(frame, -1, ConfigData())
    frame.Show()
    cfg.Show()
    app.MainLoop()
