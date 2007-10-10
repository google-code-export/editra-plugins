#!/usr/bin/env python

import wx, sys, os, crypto
import wx.lib.mixins.listctrl as listmix
import FileIcons
import SVN, CVS, GIT

_ = wx.GetTranslation

# ConfigDialogg Events
cfgEVT_CONFIG_EXIT = wx.NewEventType()
EVT_CONFIG_EXIT = wx.PyEventBinder(cfgEVT_CONFIG_EXIT, 1)

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
        

class ConfigDialog(wx.Frame):
    """Dialog for configuring the Projects plugin settings"""
    def __init__(self, parent, id, data, size=wx.DefaultSize):
        wx.Frame.__init__(self, parent, id, _("Projects Configuration"), 
                              size=size, style=wx.CLOSE_BOX)

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

    ID_FILE_FILTERS = wx.NewId()
    ID_SYNC_WITH_NOTEBOOK = wx.NewId()
    ID_DIFF_PROGRAM = wx.NewId()
    ID_BUILTIN_DIFF = wx.NewId()
    ID_EXTERNAL_DIFF = wx.NewId()

    def __init__(self, parent, id, data):
        wx.Panel.__init__(self, parent, id)
        self._data = data
        
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        flags = wx.SizerFlags().Left().Expand().Border(wx.ALL, 6)
        sizer.AddF(wx.StaticText(self, -1, _('File Filters')), flags)
        filters = wx.TextCtrl(self, self.ID_FILE_FILTERS, ' '.join(data.getFilters()), size=(-1, 100), style=wx.TE_MULTILINE)
        sizer.AddF(filters, flags)
        if wx.Platform == '__WXMAC__':
            filters.MacCheckSpelling(False)
        tt = wx.ToolTip(_("Space separated list of files patterns to exclude from view"
                          "\nThe use of wildcards (*) are permitted."))
        filters.SetToolTip(tt)
        sizer.AddF(wx.StaticBox(self, -1, size=(-1, 1)), wx.SizerFlags().Center().Expand().Border(wx.TOP|wx.BOTTOM, 10))
        sync = wx.CheckBox(self, self.ID_SYNC_WITH_NOTEBOOK, _('Keep project tree synchronized with editor notebook'))
        sync.SetValue(data.getSyncWithNotebook())
        sizer.AddF(sync, flags)
        sizer.AddF(wx.StaticBox(self, -1, size=(-1, 1)), wx.SizerFlags().Center().Expand().Border(wx.TOP|wx.BOTTOM, 10))
        sizer.AddF(wx.StaticText(self, -1, _('Diff Program')), flags)
        builtin = wx.RadioButton(self, self.ID_BUILTIN_DIFF, _('Built-in'))
        builtin.SetValue(data.getBuiltinDiff())
        sizer.AddF(builtin, flags.Border(wx.TOP|wx.LEFT, 6))
        
        # Radio button with file selector
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        external = wx.RadioButton(self, self.ID_EXTERNAL_DIFF, '')
        external.SetValue(not data.getBuiltinDiff())
        hsizer.AddF(external, wx.SizerFlags().Left().Border(wx.TOP|wx.BOTTOM|wx.LEFT, 6))
        hsizer.AddF(wx.FilePickerCtrl(self, self.ID_DIFF_PROGRAM, data.getDiffProgram(),
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
        
        # Event Handlers
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnFileChange)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheck)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnSelect)
        self.Bind(wx.EVT_TEXT, self.OnTextChange)
        
    def OnFileChange(self, evt):
        obj, id = evt.GetEventObject(), evt.GetId()
        if id == self.ID_DIFF_PROGRAM:
            path = obj.GetPath()
            if path:
                self._data.setDiffProgram(path)
            self.FindWindowById(self.ID_EXTERNAL_DIFF).SetValue(not(not(path)))
            self.FindWindowById(self.ID_BUILTIN_DIFF).SetValue(not(path))
        else:
            evt.Skip()
            
    def OnTextChange(self, evt):
        obj, id = evt.GetEventObject(), evt.GetId()
        if id == self.ID_FILE_FILTERS:
            self._data.setFilters([x.strip() for x in obj.GetValue().split() if x.strip()])        
        else:
            evt.Skip()

    def OnCheck(self, evt):
        obj, id = evt.GetEventObject(), evt.GetId()
        if id == self.ID_SYNC_WITH_NOTEBOOK:
            self._data.setSyncWithNotebook(obj.GetValue())
        else:
            evt.Skip()

    def OnSelect(self, evt):
        obj, id = evt.GetEventObject(), evt.GetId()
        if id == self.ID_BUILTIN_DIFF:
            self._data.setBuiltinDiff(True)
            self.FindWindowById(self.ID_EXTERNAL_DIFF).SetValue(False)
        elif id == self.ID_EXTERNAL_DIFF:
            self._data.setBuiltinDiff(False)
            self.FindWindowById(self.ID_BUILTIN_DIFF).SetValue(False)
        else:
            evt.Skip()
      

class SourceControlConfigTab(wx.Panel):

    ID_SC_CHOICE = wx.NewId()
    ID_SC_COMMAND = wx.NewId()
    ID_SC_REP_CHOICE = wx.NewId()
    ID_SC_USERNAME = wx.NewId()
    ID_SC_PASSWORD = wx.NewId()
    ID_SC_ENVIRONMENT = wx.NewId()
    ID_SC_ADD_ENV = wx.NewId()
    ID_SC_REMOVE_ENV = wx.NewId()

    def __init__(self, parent, id, data):
        wx.Panel.__init__(self, parent, id)
        self._data = data
        
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        flags = wx.SizerFlags().Left().Border(wx.ALL, 6)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddF(wx.Choice(self, self.ID_SC_CHOICE, 
                              choices=sorted([x for x in data.getSCSystems()])), 
                              flags.Border(wx.ALL,5))
        hsizer.AddF(wx.FilePickerCtrl(self, self.ID_SC_COMMAND), wx.SizerFlags(1))        
        sizer.AddF(hsizer, wx.SizerFlags(1).Expand())
        
        # Repository configuration box
        repsizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, _('Repository Configuration')), wx.VERTICAL)

        # Repository selector
        repsizer.AddF(wx.Choice(self, self.ID_SC_REP_CHOICE), flags.Expand())
        
        # Username and password
        userpass = wx.FlexGridSizer(2,2)
        userpass.AddGrowableCol(1,1)
        userpass.AddF(wx.StaticText(self, -1, _('Username')), flags)
        userpass.AddF(wx.TextCtrl(self, self.ID_SC_USERNAME), flags)
        userpass.AddF(wx.StaticText(self, -1, _('Password')), flags)
        userpass.AddF(wx.TextCtrl(self, self.ID_SC_PASSWORD, style=wx.TE_PASSWORD), flags)
        repsizer.AddF(userpass, wx.SizerFlags(1).Expand())
        repsizer.AddF(wx.StaticBox(self, -1, size=(-1, 1)), wx.SizerFlags().Center().Expand().Border(wx.TOP|wx.BOTTOM, 10))

        # Environment variables
        repsizer.AddF(wx.StaticText(self, -1, _('Environment Variables')), flags)
        env = AutoWidthListCtrl(self, self.ID_SC_ENVIRONMENT, size=(-1,80), 
                                style=wx.LC_REPORT|wx.LC_SORT_ASCENDING|wx.LC_VRULES|wx.LC_EDIT_LABELS)
        env.InsertColumn(0, _("Name"))
        env.InsertColumn(1, _("Value"))
        repsizer.AddF(env, flags.Expand())

        # Add env variable buttons
        envbtns = wx.BoxSizer(wx.HORIZONTAL)
        envbtns.AddF(wx.BitmapButton(self, self.ID_SC_ADD_ENV, FileIcons.getPlusBitmap()), wx.SizerFlags(0))
        envbtns.AddF(wx.BitmapButton(self, self.ID_SC_REMOVE_ENV, FileIcons.getMinusBitmap()), wx.SizerFlags(0))
        repsizer.AddF(envbtns, flags.Expand())

        sizer.AddF(repsizer, flags)

        # Extra space at bottom of panel
        #sizer.AddF(wx.Panel(self, -1), wx.SizerFlags().Border(wx.TOP, 5))

        # Add space around the sides
        outsizer = wx.BoxSizer(wx.HORIZONTAL)
        outsizer.AddF(wx.Panel(self, -1, size=(10,5)), wx.SizerFlags(0))
        outsizer.AddF(sizer, wx.SizerFlags(1).Expand())
        outsizer.AddF(wx.Panel(self, -1, size=(10,5)), wx.SizerFlags(0))

        self.SetSizer(outsizer)
        self.SetInitialSize()
        
        # Initialize controls
        self.populateSystemOptions()
        
        # Set up event handlers
        self.Bind(wx.EVT_CHOICE, self.OnChoiceSelected)
        self.Bind(wx.EVT_TEXT, self.OnTextChange)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnFileChange)
        self.Bind(wx.EVT_BUTTON, self.OnButtonPress)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnEndEdit)

    @property
    def currentSystem(self):
        return self.FindWindowById(self.ID_SC_CHOICE).GetStringSelection()

    @property
    def currentRepository(self):
        return self.FindWindowById(self.ID_SC_REP_CHOICE).GetStringSelection()
    
    def populateSystemOptions(self):
        sc, rep = self.currentSystem, self.currentRepository
        self.populateRepositoryList()
        try: command = self._data.getSCCommand(sc)
        except KeyError: command = ''
        self.FindWindowById(self.ID_SC_COMMAND).SetPath(command)

    def populateEnvironment(self):
        sc, rep = self.currentSystem, self.currentRepository
        envlist = self.FindWindowById(self.ID_SC_ENVIRONMENT)
        envlist.DeleteAllItems()        
        try: env = self._data.getSCEnvVars(sc, rep)
        except KeyError: env = {}
        for name, value in sorted(env.items()):
            index = envlist.InsertStringItem(sys.maxint, '')
            envlist.SetStringItem(index, 0, name)
            envlist.SetStringItem(index, 1, value)

    def populateUserInfo(self):
        sc, rep = self.currentSystem, self.currentRepository
        try: username = self._data.getSCUsername(sc, rep)
        except KeyError: username = ''
        self.FindWindowById(self.ID_SC_USERNAME).SetValue(username)
        try: 
            password = self._data.getSCPassword(sc, rep)
            if password:
                password = crypto.Decrypt(password, self._data.salt)
        except KeyError: password = ''
        self.FindWindowById(self.ID_SC_PASSWORD).SetValue(password)

    def populateRepositoryList(self):
        sc = self.currentSystem
        rep = self.FindWindowById(self.ID_SC_REP_CHOICE)
        rep.Clear()
        items = ['Default'] + \
                sorted([x for x in self._data.getSCRepositories(sc).keys() if x != 'Default']) + \
                ['','Add Repository...','Remove Repository...']
        for item in items:
            rep.Append(item)
        rep.SetSelection(0)
        self.populateEnvironment()
        self.populateUserInfo()
    
    def OnTextChange(self, evt):
        obj, id = evt.GetEventObject(), evt.GetId()
        sc, rep = self.currentSystem, self.currentRepository
        # Change username
        if id == self.ID_SC_USERNAME:
            value = obj.GetValue().strip()
            if not value:
                self._data.removeSCUsername(sc, rep)
            else:
                self._data.setSCUsername(sc, rep, value)
        # Change password
        elif id == self.ID_SC_PASSWORD:
            value = obj.GetValue().strip()
            if not value:
                self._data.removeSCPassword(sc, rep)
            else:
                self._data.setSCPassword(sc, rep, value)
        else:
            evt.Skip()
        
    def OnFileChange(self, evt):
        obj, id = evt.GetEventObject(), evt.GetId()
        sc, rep = self.currentSystem, self.currentRepository
        if id == self.ID_SC_COMMAND:
            self._data.setSCCommand(sc, obj.GetPath().strip())
        else:
            evt.Skip()
    
    def OnButtonPress(self, evt):
        obj, id = evt.GetEventObject(), evt.GetId()
        sc, rep = self.currentSystem, self.currentRepository
        if id == self.ID_SC_ADD_ENV:
            env = self.FindWindowById(self.ID_SC_ENVIRONMENT)
            index = env.InsertStringItem(sys.maxint, '')
            env.SetStringItem(index, 0, _('*NAME*'))
            env.SetStringItem(index, 1, _('*VALUE*'))
        elif id == self.ID_SC_REMOVE_ENV:
            env = self.FindWindowById(self.ID_SC_ENVIRONMENT)
            item = -1
            items = []
            while True:
                item = env.GetNextItem(item, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
                if item == -1:
                    break
                items.append(item)
            for item in reversed(sorted(items)):
                env.DeleteItem(item)
            self.saveEnvironmentVariables()
        else:
            evt.Skip()
            
    def OnEndEdit(self, evt):
        wx.CallAfter(self.saveEnvironmentVariables)

    def saveEnvironmentVariables(self):
        sc, rep = self.currentSystem, self.currentRepository
        env = self.FindWindowById(self.ID_SC_ENVIRONMENT)
        vars = self._data.getSCEnvVars(sc, rep)
        vars.clear()
        item = -1
        save = True
        while True:
            item = env.GetNextItem(item)
            if item == -1:
                break
            name = env.GetItem(item, 0).GetText().strip()
            value = env.GetItem(item, 1).GetText().strip()
            vars[name] = value
    
    def OnChoiceSelected(self, evt):
        obj, id = evt.GetEventObject(), evt.GetId()
        sc, rep = self.currentSystem, self.currentRepository
        if id == self.ID_SC_CHOICE:
            self.populateSystemOptions()
        elif id == self.ID_SC_REP_CHOICE:
            # Empty selection
            if not obj.GetStringSelection().strip():
                obj.SetSelection(0)
                
            # Remove repository
            elif obj.GetSelection() == (obj.GetCount() - 1):
                # Default - Blank - Add - Remove: if only 4, there's nothing to remove
                if obj.GetCount() == 4:
                    obj.SetSelection(0)
                else:
                    choices = sorted([x for x in self._data.getSCRepositories(sc).keys() if x != 'Default'])
                    scd = wx.SingleChoiceDialog(self, _('Select the repository path to remove'),
                        _('Remove repository'), choices, style=wx.DEFAULT_DIALOG_STYLE|wx.OK|wx.CANCEL|wx.CENTER)
                    if scd.ShowModal() == wx.ID_OK:
                        value = scd.GetStringSelection().strip()
                        self._data.removeSCRepository(sc, value)
                    self.populateRepositoryList()

            # Add repository
            elif obj.GetSelection() == (obj.GetCount() - 2):
                ted = wx.TextEntryDialog(self, _('Please enter a repository path.  Partial paths may also be entered.'),
                     _('Add a New Repository Path'), style=wx.OK|wx.CANCEL|wx.CENTER)
                ted.SetSize((300,-1))
                if ted.ShowModal() == wx.ID_OK:
                    value = ted.GetValue().strip()
                    if value:
                        try: 
                            self._data.getSCRepository(self.currentSystem, value)
                        except KeyError:
                            self._data.addSCRepository(self.currentSystem, value) 
                        self.populateRepositoryList()
                        obj.SetStringSelection(value)
                    else:
                        obj.SetSelection(0)
                else:
                        obj.SetSelection(0)
            self.populateUserInfo()
            self.populateEnvironment()
        else:
            evt.Skip()

        
class AutoWidthListCtrl(listmix.TextEditMixin, listmix.ListCtrlAutoWidthMixin, wx.ListCtrl):
    def __init__(self, *args, **kwargs):
        wx.ListCtrl.__init__(self, *args, **kwargs)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.TextEditMixin.__init__(self)
                
    def OnLeftDown(self, evt):
        ''' Examine the click and double
        click events to see if a row has been click on twice. If so,
        determine the current row and columnn and open the editor.'''
        from bisect import bisect        

        if self.editor.IsShown():
            self.CloseEditor()
            
        x,y = evt.GetPosition()
        row,flags = self.HitTest((x,y))
        if row != self.curRow: # self.curRow keeps track of the current row
            evt.Skip()
            return
            
        # >>> Make sure that an item is selected first
        if not self.GetSelectedItemCount():
            evt.Skip()
            return
        # <<<
        
        # the following should really be done in the mixin's init but
        # the wx.ListCtrl demo creates the columns after creating the
        # ListCtrl (generally not a good idea) on the other hand,
        # doing this here handles adjustable column widths
        
        self.col_locs = [0]
        loc = 0
        for n in range(self.GetColumnCount()):
            loc = loc + self.GetColumnWidth(n)
            self.col_locs.append(loc)

        col = bisect(self.col_locs, x+self.GetScrollPos(wx.HORIZONTAL)) - 1
        self.OpenEditor(col, row)

class ConfigData(dict):
    def __init__(self, data={}):
        self['source-control'] = {}
        self['general'] = {}
        self['projects'] = {}

        self.setFilters(sorted(['CVS','dntnd','.DS_Store','.dpp','.newpp','*~',
                        '*.a','*.o','.poem','.dll','._*','.localized',
                        '.svn','*.pyc','*.bak','#*','*.pyo','*%*', '.git',
                        '*.previous','*.swp','.#*']))
        self.setBuiltinDiff(True)
        self.setDiffProgram('opendiff')
        self.setSyncWithNotebook(True)
        
        self.addSCSystem(CVS.CVS())
        self.addSCSystem(SVN.SVN())
        self.addSCSystem(GIT.GIT())
        
        self.load()
    
    @property
    def salt(self):
        return '"\x17\x9f/D\xcf'
        
    def addProject(self, path, options={}):
        self['projects'][path] = options
        
    def removeProject(self, path):
        try: del self['projects'][path]
        except KeyError: pass
    
    def getProjects(self):
        return self['projects']
        
    def getProject(self, path):
        return self['projects'][path]
        
    def setFilters(self, filters):
        self['general']['filters'] = filters
        self.updateSCSystems()
        
    def getFilters(self):
        return self['general']['filters']
        
    def setBuiltinDiff(self, bool=True):
        self['general']['built-in-diff'] = bool
        
    def getBuiltinDiff(self):
        return self['general']['built-in-diff']
        
    def setDiffProgram(self, command):
        self['general']['diff-program'] = command
        
    def getDiffProgram(self):
        return self['general']['diff-program']
        
    def setSyncWithNotebook(self, bool=True):
        self['general']['sync-with-notebook'] = bool
    
    def getSyncWithNotebook(self):
        return self['general']['sync-with-notebook']
    
    def addSCSystem(self, instance, repositories=None):
        self['source-control'][instance.name] = self.newSCSystem(instance, repositories)
        self.updateSCSystems()
        return self['source-control'][instance.name]
    
    def updateSCSystems(self):
        for key, value in self.getSCSystems().items():
            value['instance'].filters = self.getFilters()
            value['instance'].repositories = self.getSCRepositories(key)
    
    def getSCSystems(self):
        return self['source-control']

    def getSCSystem(self, name):
        return self['source-control'][name]

    def removeSCSystem(self, name):
        try: del self['source-control'][name]
        except: pass
    
    def removeSCSystem(self, name):
        del self['source-control'][name]
    
    def newSCSystem(self, instance, repositories=None):
        system = {'command':instance.command, 'instance': instance, 'repositories': {'Default':self.newSCRepository()}}
        if repositories is not None:
            system['repositories'].update(repositories)
        return system
    
    def newSCRepository(self):
        return {'username':'', 'password':'', 'env':{}}
    
    def getSCRepositories(self, sc):
        return self.getSCSystem(sc)['repositories']
        
    def getSCRepository(self, sc, rep):
        return self.getSCRepositories(sc)[rep]
        
    def addSCRepository(self, sc, name):
        self.getSCRepositories(sc)[name] = self.newSCRepository()
        
    def removeSCRepository(self, sc, name):
        try: del self.getSCRepositories(sc)[name]
        except KeyError: pass
        
    def setSCUsername(self, sc, rep, name):
        self.getSCRepository(sc, rep)['username'] = name
    
    def removeSCUsername(self, sc, rep):
        try: del self.getSCRepository(sc, rep)['username']
        except KeyError: pass
        
    def getSCUsername(self, sc, rep):
        return self.getSCRepository(sc, rep)['username']
        
    def setSCPassword(self, sc, rep, password):
        if password.strip():
            self.getSCRepository(sc, rep)['password'] = crypto.Encrypt(password, self.salt)
        else:
            self.getSCRepository(sc, rep)['password'] = ''            

    def getSCPassword(self, sc, rep):
        return self.getSCRepository(sc, rep)['password']

    def removeSCPassword(self, sc, rep):
        try: del self.getSCRepository(sc, rep)['password']
        except KeyError: pass
        
    def setSCCommand(self, sc, command):
        self.getSCSystem(sc)['command'] = command
    
    def getSCCommand(self, sc):
        return self.getSCSystem(sc)['command']

    def addSCEnvVar(self, sc, rep, name, value):
        self.getSCEnvVars(sc, rep)[name] = value
        
    def removeSCEnvVar(self, sc, rep, name):
        try: del self.getSCEnvVars(sc, rep)[name]
        except KeyError: pass
        
    def getSCEnvVars(self, sc, rep):
        return self.getSCRepository(sc, rep)['env']

    def getSCEnvVar(self, sc, rep, name):
        return self.getSCEnvVars(sc, rep)[name]
        
    def load(self):
        data = {}
        try:
            import ed_glob, util
            filename = ed_glob.CONFIG['CACHE_DIR'] + 'Projects.config'
            f = util.GetFileReader(filename)
            if f != -1:
                try: 
                    data = eval(f.read())
                    f.close()
                except:
                    f.close()
                    os.remove(filename)
        except (ImportError, OSError):
            pass
        recursiveupdate(self, data)
        self.updateSCSystems()

    def save(self):
        print repr(self)
        try:
            import ed_glob, util, stat
            filename = ed_glob.CONFIG['CACHE_DIR'] + 'Projects.config'
            f = util.GetFileWriter(filename)
            if f != -1:
                f.write(repr(self))
                f.close()
            os.chmod(filename, stat.S_IRUSR|stat.S_IWUSR)
        except (ImportError, OSError):
            pass

def recursiveupdate(dest, src):
    """ Recursively update dst from src """
    for key, value in src.items():
        if key in dest:
            if isinstance(value, dict):
                recursiveupdate(dest[key], value)
            else:
                dest[key] = value
        else:
            dest[key] = value
    return dest

if __name__ == '__main__':
    app = wx.PySimpleApp(False)
    frame = wx.Frame(None, title="Config Dialog Parent Frame", size=(480, 335))
    cfg = ConfigDialog(frame, wx.ID_ANY, ConfigData())
    #cfg = GeneralConfigTab(frame, -1, ConfigData())
    #cfg = SourceControlConfigTab(frame, -1, ConfigData())
    frame.Show()
    cfg.Show()
    app.MainLoop()
