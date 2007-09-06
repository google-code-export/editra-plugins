#!/usr/bin/env python

import wx 
import os 
import time 
import string 
import threading 
import stat 
import fnmatch
import re 
import FileIcons
import tempfile
import subprocess
import shutil
import Trash
import wx.lib.delayedresult 
try: 
    import util         # from Editra.src
    import diffwin
except ImportError: 
    diffwin = util = None
import cfgdlg
from CVS import CVS
from GIT import GIT
from SVN import SVN
from HistWin import AdjustColour
try:
    import profiler
    eol = profiler.Profile_Get('EOL')
except ImportError:
    eol = '\n'

# Make sure that all processes use a standard shell
if wx.Platform != '__WXMAC__':
    os.environ['SHELL'] = '/bin/sh'

# Configure Platform specific commands
if wx.Platform == '__WXMAC__': # MAC
    FILEMAN = 'Finder'
    FILEMAN_CMD = 'open'
    TRASH = 'Trash'
    DIFF_CMD = 'opendiff'
elif wx.Platform == '__WXMSW__': # Windows
    FILEMAN = 'Explorer'
    FILEMAN_CMD = 'explorer'
    TRASH = 'Recycle Bin'
    DIFF_CMD = None
else: # Other/Linux
    # TODO how to check what desktop environment is in use
    # this will work for Gnome but not KDE
    FILEMAN = 'Nautilus'
    FILEMAN_CMD = 'nautilus'
    TRASH = 'Trash'
    DIFF_CMD = None
    #FILEMAN = 'Konqueror'
    #FILEMAN_CMD = 'konqueror'

ODD_PROJECT_COLOR = wx.Colour(232,239,250)
EVEN_PROJECT_COLOR = wx.Colour(232,239,250)
ODD_BACKGROUND_COLOR = wx.Colour(255,255,255)
EVEN_BACKGROUND_COLOR = wx.Colour(255,255,255)

# i18n support
_ = wx.GetTranslation

FILE_TYPES = {
    _('Text File'): {'ext':'.txt'},
    _('C File'): {'ext':'.c'},
    _('HTML File'): {'ext':'.html', 'template':'<html>\n<head><title></title></head>\n<body>\n\n</body>\n</html>'},
    _('Python File'): {'ext':'.py', 'template':'#!/usr/bin/env python\n\n'},
}
    
ID_PROJECTPANE = wx.NewId()
ID_PROJECTTREE = wx.NewId()

class SimpleEvent(wx.PyCommandEvent):
    """Event to signal that nodes need updating"""
    def __init__(self, etype, eid, value=[]):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._etype = etype
        self._id = eid
        self._value = value

    def GetEvtType(self):
        return self._etype

    def GetId(self):
        return self._id

    def GetValue(self):
        return self._value

ppEVT_SYNC_NODES = wx.NewEventType()
EVT_SYNC_NODES = wx.PyEventBinder(ppEVT_SYNC_NODES, 1)
class SyncNodesEvent(SimpleEvent):
    pass

ppEVT_UPDATE_STATUS = wx.NewEventType()
EVT_UPDATE_STATUS = wx.PyEventBinder(ppEVT_UPDATE_STATUS, 1)
class UpdateStatusEvent(SimpleEvent):
    pass

class MyTreeCtrl(wx.TreeCtrl):

    def __init__(self, parent, id, pos, size, style, log):
        wx.TreeCtrl.__init__(self, parent, id, pos, size, style)
        self.log = log

    def OnCompareItems(self, item1, item2):
        t1 = self.GetItemText(item1).lower()
        t2 = self.GetItemText(item2).lower()
        #self.log.WriteText('compare: ' + t1 + ' <> ' + t2 + '\n')
        if t1 < t2: return -1
        if t1 == t2: return 0
        return 1


class ProjectTree(wx.Panel):

    def __init__(self, parent, log):
        # Use the WANTS_CHARS style so the panel doesn't eat the Return key.
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS|wx.SUNKEN_BORDER)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.log = log
        tID = wx.NewId()

        global ODD_PROJECT_COLOR
        global EVEN_PROJECT_COLOR
        ODD_PROJECT_COLOR = EVEN_PROJECT_COLOR = AdjustColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DLIGHT), 75)

        self.tree = MyTreeCtrl(self, tID, wx.DefaultPosition, wx.DefaultSize,
                               wx.TR_DEFAULT_STYLE
                               #wx.TR_HAS_BUTTONS
                               | wx.TR_EDIT_LABELS
                               | wx.TR_MULTIPLE
                               | wx.TR_HIDE_ROOT
                               , self.log)

        # Load icons for use later
        icons = self.icons = {}
        menuicons = self.menuicons = {}

        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])

        try:
            import ed_glob
            folder = wx.ArtProvider.GetBitmap(str(ed_glob.ID_FOLDER), wx.ART_MENU)
            folderopen = wx.ArtProvider.GetBitmap(str(ed_glob.ID_OPEN), wx.ART_MENU)
            icons['folder'] = il.Add(folder)
            icons['folder-open'] = il.Add(folderopen)
            menuicons['copy'] = wx.ArtProvider.GetBitmap(str(ed_glob.ID_COPY), wx.ART_MENU)
            menuicons['cut'] = wx.ArtProvider.GetBitmap(str(ed_glob.ID_CUT), wx.ART_MENU)
            menuicons['paste'] = wx.ArtProvider.GetBitmap(str(ed_glob.ID_PASTE), wx.ART_MENU)
            menuicons['delete'] = wx.ArtProvider.GetBitmap(str(ed_glob.ID_DELETE), wx.ART_MENU)

        except ImportError:
            folder = wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, isz)
            folderopen = wx.ArtProvider_GetBitmap(wx.ART_FOLDER_OPEN, wx.ART_OTHER, isz)
            icons['folder'] = il.Add(folder)
            icons['folder-open'] = il.Add(folderopen)
            menuicons['copy'] = wx.ArtProvider_GetBitmap(wx.ART_COPY, wx.ART_OTHER, isz)
            menuicons['cut'] = wx.ArtProvider_GetBitmap(wx.ART_CUT, wx.ART_OTHER, isz)
            menuicons['paste'] = wx.ArtProvider_GetBitmap(wx.ART_PASTE, wx.ART_OTHER, isz)
            menuicons['delete'] = wx.ArtProvider_GetBitmap(wx.ART_DELETE, wx.ART_OTHER, isz)

        menuicons['blank'] = FileIcons.getBlankBitmap()
        menuicons['sc-commit'] = FileIcons.getScCommitBitmap()
        menuicons['sc-add'] = FileIcons.getScAddBitmap()
        menuicons['sc-diff'] = FileIcons.getScDiffBitmap()
        menuicons['sc-history'] = FileIcons.getScHistoryBitmap()
        menuicons['sc-remove'] = FileIcons.getScRemoveBitmap()
        menuicons['sc-status'] = FileIcons.getScStatusBitmap()
        menuicons['sc-update'] = FileIcons.getScUpdateBitmap()
        menuicons['sc-revert'] = FileIcons.getScRevertBitmap()

        icons['file'] = il.Add(FileIcons.getFileBitmap())
        
        # Create badged icons
        for badge in ['uptodate','modified','conflict','added']:
            badgeicon = getattr(FileIcons, 'getBadge'+badge.title()+'Bitmap')().ConvertToImage()
            badgeicon.Rescale(11, 11, wx.IMAGE_QUALITY_HIGH)
            for type in ['file','folder','folder-open']:
                icon = wx.MemoryDC()
                if type == 'file':
                    icon.SelectObject(FileIcons.getFileBitmap())
                elif type == 'folder':
                    icon.SelectObject(folder)
                else:
                    icon.SelectObject(folderopen)
                icon.SetBrush(wx.TRANSPARENT_BRUSH)
                icon.DrawBitmap(wx.BitmapFromImage(badgeicon), 5, 5, True)
                tbmp = icon.GetAsBitmap()
                icon.SelectObject(wx.NullBitmap)
                icons[type+'-'+badge] = il.Add(tbmp)

        icons['project-add'] = il.Add(FileIcons.getProjectAddBitmap())
        icons['project-delete'] = il.Add(FileIcons.getProjectDeleteBitmap())

        self.tree.SetImageList(il)
        self.il = il
        
        #
        # Setup default configuration
        #
        
        # Names of files to filter out of tree
        self.filters = sorted(['CVS','dntnd','.DS_Store','.dpp','.newpp','*~',
                        '*.a','*.o','.poem','.dll','._*','.localized',
                        '.svn','*.pyc','*.bak','#*','*.pyo','*%*', '.git',
                        '*.previous','*.swp','.#*'])
        
        # Commands for external programs
        self.commands = {}
        
        # Setup builtin or external diff program
        self.useBuiltinDiff = True
        if DIFF_CMD:
            self.commands['diff'] = DIFF_CMD
            self.useBuiltinDiff = False

        # Keep tree view synchronized with notebook
        self.syncWithNotebook = True
        
        # Create source control objects
        self.sourceControl = {'cvs': CVS(), 'git' : GIT(), 'svn': SVN()}
        for key, value in self.sourceControl.items():
            value.filters = self.filters

        # End configuration
        
        # Threads that watch directories corresponding to open folders
        self.watchers = {}
        
        # Temporary directory for all working files
        self.tempdir = None
        
        # Information for copy/cut/paste of files
        self.clipboard = {'files':[], 'delete':False}
        
        # Notebook tab is opening because another was closed
        self.isClosing = False
        
        # Number of seconds to allow a source control command to run
        # before timing out
        self.scTimeout = 60
        
        # Storage for currently running source control threads
        self.scThreads = {}
        
        # Create root of tree
        self.root = self.tree.AddRoot('Projects')
        self.tree.SetPyData(self.root, None)
        self.tree.SetItemImage(self.root, self.icons['folder'], wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root, self.icons['folder-open'], wx.TreeItemIcon_Expanded)

        # Load configuration settings
        self.loadSettings()

        # Bind events
        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.OnItemExpanded, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.OnItemCollapsed, self.tree)
        #self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, self.tree)
        #self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginEdit, self.tree)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndEdit, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivate, self.tree)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(EVT_SYNC_NODES, self.OnSyncNode)
        self.Bind(EVT_UPDATE_STATUS, self.OnUpdateStatus)
        
        try:
            import ed_event
            import extern.flatnotebook as fnb
            #self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGING,
            mw = self.GetGrandParent()
            mw.nb.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
            mw.nb.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnPageClosing)
            mw.Bind(ed_event.EVT_MAINWINDOW_EXIT, self.OnMainWindowExit)
        except ImportError: pass

        #self.tree.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        #self.tree.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        #self.tree.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)

    def readConfig(self):
        """ Read config settings into a dictionary """
        config = {}
        try:
            import ed_glob, util
            f = util.GetFileReader(ed_glob.CONFIG['CACHE_DIR'] + 'Projects.config')
            if f != -1:
                current = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    elif line.startswith('[') and line.endswith(']'):
                        current = config[line[1:-1].strip()] = []
                    else:
                        current.append(line) 
                f.close()
        except (ImportError, OSError):
            pass
        return config

    def writeConfig(self, **kwargs):
        """
        Write keyword arguments into config dictionary
       
        Each keyword argument is written into its own section in the 
        configuration.  When being read back out, the resulting dictionary
        will have a key for each keyword argument and the value will 
        always be a list of the given values.

        """
        try:
            import ed_glob, util
            config = self.readConfig()
            config.update(kwargs)
            f = util.GetFileWriter(ed_glob.CONFIG['CACHE_DIR'] + 'Projects.config')
            if f != -1:
                for key, value in config.items():
                    f.write('[%s]\n' % key)
                    if isinstance(value, (list,tuple)):
                        for v in value:
                            f.write('%s\n' % v)
                    else:
                        f.write('%s\n' % value)
                f.close()
        except (ImportError, OSError):
            pass

    def loadSettings(self):
        """ Load projects from config file """
        config = self.readConfig()
        for p in config.get('projects',[]):
            self.addProject(p, save=False)

        self.filters = sorted(config.get('filters', self.filters))

        for c in config.get('commands',[]):
            key, value = c.split(' ', 1)
            self.commands[key] = value

        for c in config.get('sourcecontrol',[]):
            key, value = c.split(' ', 1)
            self.sourceControl[key].command = value
        
        for c in config.get('syncwithnotebook',[]):
            if 'yes' in c:
                self.syncWithNotebook = True
            else:
                self.syncWithNotebook = False

        for c in config.get('usebuiltindiff',[]):
            if 'yes' in c:
                self.useBuiltinDiff = True
            else:
                self.useBuiltinDiff = False

    def saveSettings(self):
        """ Save all settings """
        self.saveProjects()
        self.saveFilters()
        self.saveCommands()
        self.saveSourceControl()
        self.saveSyncWithNotebook()
        self.saveUseBuiltinDiff()

    def saveProjects(self):
        """ Save projects to config file """
        self.writeConfig(projects=self.getProjectPaths())

    def saveFilters(self):
        self.writeConfig(filters=sorted(self.filters))

    def saveSyncWithNotebook(self):
        if self.syncWithNotebook:
            self.writeConfig(syncwithnotebook=['yes'])
        else:
            self.writeConfig(syncwithnotebook=['no'])
        
    def saveUseBuiltinDiff(self):
        if self.useBuiltinDiff:
            self.writeConfig(usebuiltindiff=['yes'])
        else:
            self.writeConfig(usebuiltindiff=['no'])
        
    def saveCommands(self):
        commands = []
        for key, value in self.commands.items():
            commands.append('%s %s' % (key, value))
        self.writeConfig(commands=commands)

    def saveSourceControl(self):
        commands = []
        for key, value in self.sourceControl.items():
            commands.append('%s %s' % (key, value.command))
        self.writeConfig(sourcecontrol=commands)

    def addProject(self, path, save=True):
        """
        Add a project for the given path
        
        Required Arguments:
        path -- full path to the project directory
        
        Returns: tree node for the project
        
        """
        node = self.tree.AppendItem(self.tree.GetRootItem(), os.path.basename(path))
        proj = self.tree.AppendItem(node, '')
        self.tree.AppendItem(proj, '')  # <- workaround for windows
        self.tree.SetItemHasChildren(node)
        self.tree.SetPyData(node, {'path':path})
        self.tree.SetItemImage(node, self.icons['folder'], wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(node, self.icons['folder-open'], wx.TreeItemIcon_Expanded)
        if save:
            self.saveProjects()
        self.tree.SetItemBold(node)
        if not(self.tree.GetChildrenCount(self.root, False) % 2):
            self.tree.SetItemBackgroundColour(node, ODD_PROJECT_COLOR)
        else:
            self.tree.SetItemBackgroundColour(node, EVEN_PROJECT_COLOR)
        return node

    def removeSelectedProject(self):
        """ Remove the selected project """
        projects = self.getChildren(self.root)
        for project in self.tree.GetSelections():
            if project in projects:
                self.tree.CollapseAllChildren(project)
                self.tree.Delete(project)
        self.saveProjects()

    def getProjectPaths(self):
        """ Get the paths for all projects """
        paths = []
        for child in self.getChildren(self.root):
            paths.append(self.tree.GetPyData(child)['path'])
        return paths

    def getChildren(self, parent):
        """
        Return a list of children for the given node
                
        Required Arguments:
        parent -- node to search
        
        Returns: list of child nodes
        
        """
        children = []
        child, cookie = self.tree.GetFirstChild(parent)
        if child:
            children.append(child)
            while True:
                child, cookie = self.tree.GetNextChild(parent, cookie)
                if not child:
                    break
                children.append(child)
        return children

    def OnSyncNode(self, evt):
        """
        Synchronize the tree nodes with the file system changes
        
        Required Arguments:
        added -- files that were added
        modified -- files that were modified
        deleted -- files that were deleted
        parent -- tree node corresponding to the directory
        
        """            
        added, modified, deleted, parent = evt.GetValue()
        children = {}
        for child in self.getChildren(parent):
            children[self.tree.GetItemText(child)] = child
            
        # Sort so that files in directories get operated on
        # before the directories themselves
        added = list(reversed(sorted(added)))
        modified = list(reversed(sorted(modified)))
        deleted = list(reversed(sorted(deleted)))

        updates = []
            
        if children:
            for item in deleted:
                if item in children:
                    node = children[item]
                    if os.path.isdir(self.tree.GetPyData(node)['path']):
                        self.tree.Collapse(node)
                    self.tree.Delete(node)                    

            # Update status on modified files
            for item in modified:
                if item not in children:
                    continue
                updates.append(children[item])

        for item in added:
            if os.path.basename(item) not in children:
                updates.append(self.addPath(parent, item))

        # Update tree icons
        items = []
        for item in updates:
            try:
                if not os.path.isdir(self.tree.GetPyData(item)['path']):
                    items.append(item)
            except ValueError: pass
        if items:
            self.scStatus(items)
        
        self.tree.SortChildren(parent)
        
        evt.Skip()

    def getSelectedNodes(self):
        return self.tree.GetSelections()
                        
    def getSelectedPaths(self):
        """ Get paths associated with selected items """
        paths = []
        for item in self.getSelectedNodes():
            paths.append(self.tree.GetPyData(item)['path'])
        return paths
        
    def OnMainWindowExit(self, evt):
        """ Shutdown threads when main window closes """
        evt.Skip()
    
    def OnPageClosing(self, evt):
        """ Notebook tab was closed """
        self.isClosing = True
        evt.Skip()
        
    def OnPageChanged(self, evt):
        """ Notebook tab was changed """
        evt.Skip()

        if not self.syncWithNotebook:
            return

        # Don't sync when a tab was just closed
        if self.isClosing:
            self.isClosing = False
            return
        
        notebook = evt.GetEventObject()
        pg_num = evt.GetSelection()
        txt_ctrl = notebook.GetPage(pg_num)

        # With the text control (ed_stc.EDSTC) this will return the full path of the file or 
        # a wx.EmptyString if the buffer does not contain an on disk file
        filename = txt_ctrl.GetFileName()
        
        if filename in self.getSelectedPaths():
            return
        
        for project in self.getChildren(self.root):
            dir = path = self.tree.GetPyData(project)['path']
            if not os.path.isdir(dir):
                dir = os.path.dirname(dir)
            if not dir.endswith(os.sep):
                dir += os.sep
            if filename.startswith(dir):
                filename = filename[len(dir):].split(os.sep)
                self.tree.Expand(project)
                folder = project
                try:
                    while filename:
                        name = filename.pop(0)
                        for item in self.getChildren(folder):
                            if self.tree.GetItemText(item) == name:
                                self.tree.Expand(item)
                                folder = item
                                continue
                except: pass
                self.tree.UnselectAll()
                self.tree.SelectItem(folder)
                break

    def OnRightDown(self, event):
        pt = event.GetPosition()
        item, flags = self.tree.HitTest(pt)
        if item:
            self.log.WriteText("OnRightClick: %s, %s, %s\n" %
                               (self.tree.GetItemText(item), type(item), item.__class__))
            self.tree.SelectItem(item)

    def OnRightUp(self, event):
        pt = event.GetPosition()
        item, flags = self.tree.HitTest(pt)
        if item:        
            self.log.WriteText("OnRightUp: %s (manually starting label edit)\n"
                               % self.tree.GetItemText(item))
            self.tree.EditLabel(item)

    def OnBeginEdit(self, event):
        self.log.WriteText("OnBeginEdit\n")
 
    def OnEndEdit(self, event):
        """ Finish editing tree node label """
        if event.IsEditCancelled():
            return
        node = event.GetItem()
        data = self.tree.GetPyData(node)
        path = data['path']
        newpath = os.path.join(os.path.dirname(path),event.GetLabel())
        try: 
            os.rename(path, newpath)
            data['path'] = newpath
        except OSError: pass

    def OnLeftDClick(self, event):
        pt = event.GetPosition();
        item, flags = self.tree.HitTest(pt)
        if item:
            self.log.WriteText("OnLeftDClick: %s\n" % self.tree.GetItemText(item))
            parent = self.tree.GetItemParent(item)
            if parent.IsOk():
                self.tree.SortChildren(parent)
        event.Skip()

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.tree.SetDimensions(0, 0, w, h)

    def OnItemExpanded(self, event):
        """
        When an item is expanded, track the contents of that directory
        
        """
        parent = event.GetItem()
        if not parent: return
        path = self.tree.GetPyData(parent)['path']
        for item in os.listdir(path):
            self.addPath(parent, item)
        # Delete dummy node from self.addFolder
        self.tree.Delete(self.tree.GetFirstChild(parent)[0])
        self.tree.SortChildren(parent)
        self.addDirectoryWatcher(parent)
        self.scStatus([parent])
        
    def getSCSystem(self, path):
        """ Determine source control system being used on path if any """
        sc = None
        for key, value in self.sourceControl.items():
            if value.isControlled(path):
                return value            

    def scAdd(self, nodes):
        self.scCommand(nodes, 'add')

    def scRemove(self, nodes):
        self.scCommand(nodes, 'remove')

    def scUpdate(self, nodes):
        self.scCommand(nodes, 'update')

    def scRevert(self, nodes):
        self.scCommand(nodes, 'revert')

    def scCheckout(self, nodes):
        self.scCommand(nodes, 'checkout') 

    def scStatus(self, nodes):
        self.scCommand(nodes, 'status') 
        
    def scHistory(self, nodes):
        """ Open source control history window """
        if not nodes:
            return
        from HistWin import HistoryWindow
        for node in self.getSelectedNodes():
            path = self.tree.GetPyData(node)['path']
            win = HistoryWindow(self, path, self, node, path)
            win.Show()
        
    def scCommit(self, nodes, **options): 
        """ Commit files to source control """
        while True:
            paths = list()
            for node in nodes:
                try: data = self.tree.GetPyData(node)
                except: data = {}
                if data.get('sclock', None):
                    continue
                if 'path' not in data:
                    continue
                else:
                    paths.append(data['path'])

            ted = CommitDialog(self, _("Commit Dialog"), 
                               _("Enter your commit message:"), paths)
            if ted.ShowModal() != wx.ID_OK:
                return
            message = ted.GetValue().strip().replace('"', '\\"')
            if message:
                break
        self.scCommand(nodes, 'commit', message=message)

    def scCommand(self, nodes, command, callback=None, **options):
        """
        Run a source control command 
        
        Required Arguments:
        nodes -- selected tree nodes
        command -- name of command type to run
        
        """
        try: self.GetParent().StartBusy()
        except: pass
        
        def run(callback, nodes, command, **options):
            concurrentcmds = ['status','history']
            NODE, DATA, SC = 0, 1, 2
            nodeinfo = []
            for node in nodes:                
                # Get node data
                try: data = self.tree.GetPyData(node)
                except: data = {}
                
                # node, data, sc
                info = [node, data, None]
                
                # See if the node already has an operation running
                if data.get('sclock', None):
                    return wx.MessageDialog(self, 
                                            _('There is already a source control ' \
                                              'command executing on this path.  ' \
                                              'Please wait for it to finish before ' \
                                              'attempting more operations.'),
                                            _('Source control directory is busy'), 
                                            style=wx.OK|wx.ICON_ERROR).ShowModal()

                # See if the node has a path associated
                # Technically, all nodes should (except the root node)
                if 'path' not in data:
                    continue

                # Determine source control system
                sc = self.getSCSystem(data['path'])
                if sc is None:
                    if os.path.isdir(data['path']) or command == 'add':
                        sc = self.getSCSystem(os.path.dirname(data['path']))
                        if sc is None:
                            continue
                    else:
                        continue
                info[SC] = sc
                
                nodeinfo.append(info)
                
            # Lock node while command is running
            if command not in concurrentcmds:
                for node, data, sc in nodeinfo:
                    data['sclock'] = command

            rc = True            
            try:
                # Find correct method
                method = getattr(sc, command, None)
                if method:
                    # Run command (only if it isn't the status command)
                    if command != 'status':
                        rc = self._timeoutCommand(callback, method, 
                             [x[DATA]['path'] for x in nodeinfo], **options)

            finally:
                # Only update status if last command didn't time out
                if command not in ['history','revert','update'] and rc:
                    for node, data, sc in nodeinfo:
                        self._updateStatus(node, data, sc)

                # Unlock
                if command not in concurrentcmds:
                    for node, data, sc in nodeinfo:
                        del data['sclock'] 
                            
        wx.lib.delayedresult.startWorker(self.endSCCommand, run, 
                                         wargs=(callback, nodes, command), 
                                         wkwargs=options)
                                         
    def _timeoutCommand(self, callback, *args, **kwargs):
        """ Run command, but kill it if it takes longer than `timeout` secs """
        result = []
        def resultWrapper(result, *args, **kwargs):
            """ Function to catch output of threaded method """
            args = list(args)
            method = args.pop(0)
            result.append(method(*args, **kwargs))

        # Insert result object to catch output
        args = list(args)
        args.insert(0, result)    

        # Start thread
        t = threading.Thread(target=resultWrapper, args=args, kwargs=kwargs)
        t.start()
        self.scThreads[t] = True
        t.join(self.scTimeout)
        del self.scThreads[t]
        
        if t.isAlive():
            t._Thread__stop()
            #print 'COMMAND TIMED OUT'
            return False
        #print 'COMMAND SUCCEEDED'
        if callback is not None:
            callback(result[0])
        return True
        
    def _updateStatus(self, node, data, sc):
        """
        Update the icons in the tree view to show the status of the files
                
        """
        # Update status of nodes
        updates = []
        try:
            status = {}
            rc = self._timeoutCommand(None, sc.status, [data['path']], status=status)
            if not rc:
                return updates
            # Update the icons for the file nodes
            if os.path.isdir(data['path']):
                for child in self.getChildren(node):
                    text = self.tree.GetItemText(child)
                    if text not in status:
                        continue
                    if os.path.isdir(os.path.join(data['path'],text)):
                        # Closed folder icon
                        icon = self.icons.get('folder-'+status[text].get('status',''))
                        if icon:                    
                            updates.append((self.tree.SetItemImage, child, icon, wx.TreeItemIcon_Normal))
                        # Open folder icon
                        icon = self.icons.get('folder-open-'+status[text].get('status',''))
                        if icon:                    
                            updates.append((self.tree.SetItemImage, child, icon, wx.TreeItemIcon_Expanded))
                        # Update children status if opened
                        if self.tree.IsExpanded(child):
                            self._updateStatus(child, self.tree.GetPyData(child), sc)
                    else:
                        icon = self.icons.get('file-'+status[text].get('status',''))
                        if icon:
                            updates.append((self.tree.SetItemImage, child, icon, wx.TreeItemIcon_Normal))
                        #if 'tag' in status[text]:
                        #    updates.append((self.tree.SetToolTip, wx.ToolTip('Tag: %s' % status[text]['tag'])))
            else:
                text = self.tree.GetItemText(node)
                if text in status:
                    icon = self.icons.get('file-'+status[text].get('status',''))
                    if icon:
                        updates.append((self.tree.SetItemImage, node, icon, wx.TreeItemIcon_Normal))
                    #if 'tag' in status[text]:
                    #    updates.append((self.tree.SetToolTip, wx.ToolTip('Tag: %s' % status[text]['tag'])))
        except (OSError, IOError):
            pass

        wx.PostEvent(self, UpdateStatusEvent(ppEVT_UPDATE_STATUS, self.GetId(), updates))

    def OnUpdateStatus(self, evt):
        """ Apply status updates to tree view """
        for update in evt.GetValue():
            update = list(update)
            method = update.pop(0)
            try: method(*update)
            except: pass
        evt.Skip()
            
    def endSCCommand(self, delayedresult):
        self.GetParent().StopBusy()
        
    def endPaste(self, delayedresult):
        self.GetParent().StopBusy()
        
    def compareRevisions(self, path, rev1=None, date1=None, rev2=None, date2=None, callback=None):
        """
        Compare the playpen path to a specific revision, or compare two revisions
        
        Required Arguments:
        path -- absolute path of file to compare
        
        Keyword Arguments:
        rev1/date1 -- first file revision/date to compare against
        rev2/date2 -- second file revision/date to campare against
        
        """
        def diff(path, rev1, date1, rev2, date2, callback):
            # Only do files
            if os.path.isdir(path):
                for file in os.listdir(path):
                    self.compareRevisions(file, rev1=rev1, date1=date1,
                                                rev2=rev2, date2=date2)
                return

            sc = self.getSCSystem(path)
            if sc is None:
                if callback is not None:
                    callback()
                return
                
            content1 = content2 = ext1 = ext2 = None

            # Grab the first specified revision
            if rev1 or date1:
                content1 = sc.fetch([path], rev=rev1, date=date1)
                if content1 and content1[0] is None:
                    if callback is not None:
                        callback()
                    return wx.MessageDialog(self, 
                                            _('The requested file could not be ' \
                                            'retrieved from the source control system.'), 
                                            _('Could not retrieve file'), 
                                            style=wx.OK|wx.ICON_ERROR).ShowModal()
                content1 = content1[0]
                if rev1:
                    ext1 = rev1
                elif date1:
                    ext1 = date1
        
            # Grab the second specified revision
            if rev2 or date2:
                content2 = sc.fetch([path], rev=rev2, date=date2)
                if content2 and content2[0] is None:
                    if callback is not None:
                        callback()
                    return wx.MessageDialog(self, 
                                            'The requested file could not be ' +
                                            'retrieved from the source control system.', 
                                            'Could not retrieve file', 
                                            style=wx.OK|wx.ICON_ERROR).ShowModal()
                content2 = content2[0]
                if rev2:
                    ext2 = rev2
                elif date2:
                    ext2 = date2

            if not(rev1 or date1 or rev2 or date2):
                content1 = sc.fetch([path])
                if content1 and content1[0] is None:
                    if callback is not None:
                        callback()
                    return wx.MessageDialog(self, 
                                            'The requested file could not be ' +
                                            'retrieved from the source control system.', 
                                            'Could not retrieve file', 
                                            style=wx.OK|wx.ICON_ERROR).ShowModal()
                content1 = content1[0]
                ext1 = 'previous'
                
            if not self.tempdir:
                import tempfile
                self.tempdir = tempfile.mkdtemp()

            # Write temporary files
            delete = []
            path1 = path2 = None
            if content1 and content2:
                path = os.path.join(self.tempdir, os.path.basename(path))
                path1 = '%s.%s' % (path, ext1)
                path2 = '%s.%s' % (path, ext2)
                f = open(path1, 'w')
                f.write(content1)
                f.close()
                f = open(path2, 'w')
                f.write(content2)
                f.close()
            elif content1:
                path1 = path
                path = os.path.join(self.tempdir, os.path.basename(path))
                path2 = '%s.%s' % (path, ext1)
                f = open(path2, 'w')
                f.write(content1)
                f.close()
            elif content2:
                path1 = path
                path = os.path.join(self.tempdir, os.path.basename(path))
                path2 = '%s.%s' % (path, ext2)
                f = open(path2, 'w')
                f.write(content2)
                f.close()
            
            # Run comparison program
            if self.useBuiltinDiff or 'diff' not in self.commands:
                diffwin.GenerateDiff(path2, path1, html=True)
            else:
                subprocess.call([self.commands['diff'], path2, path1]) 
            
            if callback is not None:
                callback()
            
        t = threading.Thread(target=diff, args=(path, rev1, date1, rev2, date2, callback))
        t.setDaemon(True)
        t.start()        

    def compareToPrevious(self, node):
        """ Use opendiff to compare playpen version to repository version """
        path = self.tree.GetPyData(node)['path']
        # Only do files
        if os.path.isdir(path):
            for child in self.getChildren(node):
                self.compareToPrevious(child)
            return
        self.compareRevisions(path)

    def addDirectoryWatcher(self, node):                
        """
        Add a directory watcher thread to the given node
        
        Directory watchers keep tree nodes and the file system constantly in sync
        
        Required Arguments:
        node -- the tree node to keep in sync
        
        """
        data = self.tree.GetPyData(node)
        path = data['path']
        # Start a directory watcher to keep branch in sync.  When the flag variable 
        # is emptied, the thread stops.
        flag = [1]
        data['watcher'] = w = threading.Thread(target=self.watchDirectory, 
                                               args=(path,), 
                                               kwargs={'flag':flag, 'data':node})
        w.flag = flag
        w.start()
        self.watchers[w] = flag
        #print 'WATCHING', path, self.tree.GetItemText(node)

    def addPath(self, parent, name):
        """
        Add a file system path to the given node
        
        The new node can be a directory or a file.  
        Either one will be handled appropriately.
        
        Required Arguments:
        parent -- tree node to add the new node to
        name -- name of the item to add
        
        Returns: newly created node or None if the path isn't a file or 
            directory.  It will also return None if the path is being
            filtered out.
        
        """
        if name.endswith('\r'):
            return
        for pattern in self.filters:
            if fnmatch.fnmatchcase(name, pattern):
                return
        data = self.tree.GetPyData(parent)
        if data is None:
            return
        parentpath = data['path']
        itempath = os.path.join(parentpath,name)
        if os.path.isfile(itempath):
            node = self.addFile(parent, name)
        elif os.path.isdir(itempath):
            node = self.addFolder(parent, name)
        if self.tree.GetItemParent(parent) == self.root:
            if self.tree.GetItemBackgroundColour(parent) == ODD_PROJECT_COLOR:
                self.tree.SetItemBackgroundColour(node, ODD_BACKGROUND_COLOR)
            else:
                self.tree.SetItemBackgroundColour(node, EVEN_BACKGROUND_COLOR)
        else:
            self.tree.SetItemBackgroundColour(node, self.tree.GetItemBackgroundColour(parent))
        return node

    def addFolder(self, parent, name):
        """
        Add a folder to the given tree node
        
        Required Arguments:
        parent -- node to add the folder to
        name -- name of node to add
        
        Returns: newly created node
        
        """
        parentpath = self.tree.GetPyData(parent)['path']
        node = self.tree.AppendItem(parent, name)
        # Work around Windows bug where folders cannot expand unless it
        # has children.  This item is deleted when the folder is expanded.
        self.tree.AppendItem(node, '')
        self.tree.SetItemHasChildren(node)
        self.tree.SetPyData(node, {'path':os.path.join(parentpath,name)})
        self.tree.SetItemImage(node, self.icons['folder'], wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(node, self.icons['folder-open'], wx.TreeItemIcon_Expanded)
        return node

    def addFile(self, parent, name):
        """
        Add a file to the given tree node
        
        Required Arguments:
        parent -- node to add the file to
        name -- name of node to add
        
        Returns: newly created node
        
        """
        parentpath = self.tree.GetPyData(parent)['path']
        node = self.tree.AppendItem(parent, name)
        self.tree.SetPyData(node, {'path':os.path.join(parentpath,name)})
        self.tree.SetItemImage(node, self.icons['file'], wx.TreeItemIcon_Normal)
        return node

    def OnItemCollapsed(self, event):
        """
        When an item is collapsed, quit tracking the folder contents
        
        """
        item = event.GetItem()
        if not item: return
        
        # Collapse all children first so that their watchers get deleted
        self.tree.CollapseAllChildren(item)
        
        self.tree.DeleteChildren(item)
        self.tree.AppendItem(item, '')  # <- Dummy node workaround for MSW
        
        # Kill the watcher thread
        data = self.tree.GetPyData(item)
        data['watcher'].flag.pop()
        del self.watchers[data['watcher']]
        del data['watcher']

    def OnSelChanged(self, event):
        self.item = event.GetItem()
        if self.item:
            self.log.WriteText("OnSelChanged: %s\n" % self.tree.GetItemText(self.item))
            if wx.Platform == '__WXMSW__':
                self.log.WriteText("BoundingRect: %s\n" %
                                   self.tree.GetBoundingRect(self.item, True))
            #items = self.tree.GetSelections()
            #print map(self.tree.GetItemText, items)
        event.Skip()

    def OnContextMenu(self, event):
        #self.log.WriteText("OnContextMenu\n")

        # only do this part the first time so the events are only bound once
        #
        # Yet another anternate way to do IDs. Some prefer them up top to
        # avoid clutter, some prefer them close to the object of interest
        # for clarity. 
        if not hasattr(self, "popupIDEdit"):
            self.popupIDEdit = wx.NewId()
            self.popupIDOpen = wx.NewId()
            self.popupIDReveal = wx.NewId()
            self.popupIDCut = wx.NewId()
            self.popupIDCopy = wx.NewId()
            self.popupIDPaste = wx.NewId()
            self.popupIDSCRefresh = wx.NewId()
            self.popupIDSCDiff = wx.NewId()
            self.popupIDSCUpdate = wx.NewId()
            self.popupIDSCHistory = wx.NewId()
            self.popupIDSCCommit = wx.NewId()
            self.popupIDSCRemove = wx.NewId()
            self.popupIDSCRevert = wx.NewId()
            self.popupIDSCAdd = wx.NewId()
            self.popupIDDelete = wx.NewId()
            self.popupIDRename = wx.NewId()
            self.popupIDExecuteCommand = wx.NewId()
            self.popupIDNewFolder = wx.NewId()
            self.popupIDNewFile = wx.NewId()
            self.popupIDNewMenu = wx.NewId()

            self.Bind(wx.EVT_MENU, self.onPopupEdit, id=self.popupIDEdit)
            self.Bind(wx.EVT_MENU, self.onPopupOpen, id=self.popupIDOpen)
            self.Bind(wx.EVT_MENU, self.onPopupReveal, id=self.popupIDReveal)
            self.Bind(wx.EVT_MENU, self.onPopupCopy, id=self.popupIDCopy)
            self.Bind(wx.EVT_MENU, self.onPopupCut, id=self.popupIDCut)
            self.Bind(wx.EVT_MENU, self.onPopupPaste, id=self.popupIDPaste)
            self.Bind(wx.EVT_MENU, self.onPopupSCRefresh, id=self.popupIDSCRefresh)
            self.Bind(wx.EVT_MENU, self.onPopupSCDiff, id=self.popupIDSCDiff)
            self.Bind(wx.EVT_MENU, self.onPopupSCUpdate, id=self.popupIDSCUpdate)
            self.Bind(wx.EVT_MENU, self.onPopupSCHistory, id=self.popupIDSCHistory)
            self.Bind(wx.EVT_MENU, self.onPopupSCCommit, id=self.popupIDSCCommit)
            self.Bind(wx.EVT_MENU, self.onPopupSCRemove, id=self.popupIDSCRemove)
            self.Bind(wx.EVT_MENU, self.onPopupSCRevert, id=self.popupIDSCRevert)
            self.Bind(wx.EVT_MENU, self.onPopupSCAdd, id=self.popupIDSCAdd)
            self.Bind(wx.EVT_MENU, self.onPopupDelete, id=self.popupIDDelete)
            self.Bind(wx.EVT_MENU, self.onPopupRename, id=self.popupIDRename)
            self.Bind(wx.EVT_MENU, self.onPopupExecuteCommand, id=self.popupIDExecuteCommand)
            self.Bind(wx.EVT_MENU, self.onPopupNewFolder, id=self.popupIDNewFolder)

        paths = self.getSelectedPaths()

        # Do we have something to paste
        pastable = False
        if len(paths) == 1 and os.path.isdir(paths[0]):
            pastable = not(not(self.clipboard['files'])) 
        
        # Is directory controlled by source control
        scenabled = False
        for item in paths:
            if self.getSCSystem(item):
                scenabled = True
                break

        # Add or remove
        if scenabled:
            addremove = (self.popupIDSCRemove, _("Remove from repository"), 'sc-remove', True)
        else:
            addremove = (self.popupIDSCAdd, _("Add to repository"), 'sc-add', True)
            
        # New file / folder submenu
        newmenu = wx.Menu()
        newmenu.AppendItem(wx.MenuItem(newmenu, self.popupIDNewFolder, _('Folder')))
        newmenu.AppendSeparator()
        for type in FILE_TYPES:
            id = wx.NewId()
            newmenu.AppendItem(wx.MenuItem(newmenu, id, type))
            self.Bind(wx.EVT_MENU, self.onPopupNewFile, id=id)

        # make a menu
        menu = wx.Menu()
        items = [
            (self.popupIDEdit, _('Edit'), None, True),
            (self.popupIDOpen, _('Open'), None, True),
            (self.popupIDReveal, _('Open enclosing folder'), None, True),
            (self.popupIDNewMenu, _('New...'), newmenu, True),
            (None, None, None, None),
            (self.popupIDCut, _('Cut'), 'cut', True),
            (self.popupIDCopy, _('Copy'), 'copy', True),
            (self.popupIDPaste, _('Paste'), 'paste', pastable),
            (None, None, None, None),
            (self.popupIDExecuteCommand, _('Execute command...'), None, True),            
            (None, None, None, None),
            #(self.popupIDRename, _('Rename'), None, True),
            #(None, None, None, None),
            (self.popupIDSCRefresh, _("Refresh status"), 'sc-status', scenabled),
            (self.popupIDSCUpdate, _("Update"), 'sc-update', scenabled),
            (self.popupIDSCDiff, _("Compare to previous version"), 'sc-diff', scenabled),
            (self.popupIDSCHistory, _("Show revision history"), 'sc-history', scenabled),
            (self.popupIDSCCommit, _("Commit changes"), 'sc-commit', scenabled),
            (self.popupIDSCRevert, _("Revert to repository version"), 'sc-revert', scenabled),
            addremove,
            (None, None, None, None),
            (self.popupIDDelete, _("Move to "+TRASH), 'delete', True),
        ]
        for id, title, icon, enabled in items:
            if id is None:
                menu.AppendSeparator()
                continue
            elif icon is not None and not isinstance(icon, basestring):
                item = menu.AppendMenu(id, title, icon)
                item.SetBitmap(self.menuicons['blank'])
                continue
            item = wx.MenuItem(menu, id, _(title))
            if icon: 
                item.SetBitmap(self.menuicons[icon])
            else:
                item.SetBitmap(self.menuicons['blank'])
            item.Enable(enabled)
            menu.AppendItem(item)

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()
        
    def onPopupNewFolder(self, event):
        """ Create a new folder """
        node = self.getSelectedNodes()[0]
        path = self.tree.GetPyData(node)['path']
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        newpath = os.path.join(path, 'untitled folder')
        i = 1
        while os.path.exists(newpath):
            newpath = re.sub(r'-\d+$', r'', newpath)
            newpath += '-%d' % i
            i += 1
            print newpath
        print newpath
        os.makedirs(newpath)

    def onPopupNewFile(self, event):
        """ Create a new file """
        node = self.getSelectedNodes()[0]
        path = self.tree.GetPyData(node)['path']
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        print path
        # Determine file type
        id = event.GetId()
        menu = event.GetEventObject()
        key = None
        for item in menu.GetMenuItems():
            if item.GetId() == id:
                key = item.GetLabel()
                break
        if not key or key not in FILE_TYPES:
            return
            
        # Get informatio about file type
        info = FILE_TYPES[key]
        
        # Create unique name
        newpath = os.path.join(path, 'untitled file'+info['ext'])
        i = 1
        while os.path.exists(newpath):
            newpath = os.path.splitext(newpath)[0]
            newpath = re.sub(r'-\d+$', r'', newpath)
            newpath += '-%d%s' % (i, info['ext'])
            i += 1
        
        # Write template info
        f = open(newpath, 'w')
        f.write(info.get('template','').replace('\n',eol))
        f.close()

    def onPopupEdit(self, event):
        """ Open the current file in the editor """
        return self.OnActivate(event)
        
    def onPopupExecuteCommand(self, event):
        """ Execute commands on file system tree """
    
        ted = wx.TextEntryDialog(self, 
              _('The following command will be executed on all selected\n' \
                'files and files contained in selected directories.'),
              _('Enter command to execute on all files'))

        if ted.ShowModal() != wx.ID_OK:
            return

        command = ted.GetValue().strip()
        if not command:
            return

        for item in self.getSelectedPaths():
            if os.path.isdir(item):
                for root, dirs, files in os.walk(item):
                    for f in files:
                        #print command, os.path.join(root,f)
                        os.system('%s "%s"' % (command, os.path.join(root,f))) 
            else:
                #print command, item
                os.system('%s "%s"' % (command, item)) 

    def onPopupOpen(self, event):
        """ Open the current file using Finder """
        for file in self.getSelectedPaths():
            subprocess.call([FILEMAN_CMD, file])

    def onPopupReveal(self, event):
        """ Open the Finder to the parent directory """
        for file in self.getSelectedPaths():
            subprocess.call([FILEMAN_CMD, os.path.dirname(file)])

    def onPopupRename(self, event):
        """ Rename the current selection """
        for node in self.getSelectedNodes():
            self.tree.EditLabel(node)

    def onPopupSCDiff(self, event):
        """ Diff the file to the file in the repository """
        for node in self.getSelectedNodes():
            self.compareToPrevious(node)
            
    def onPopupCut(self, event):
        """ Cut the files to the clipboard """
        self.clipboard['files'] = self.getSelectedPaths()
        self.clipboard['delete'] = True
        for item in self.getSelectedNodes():
            self.tree.SetItemTextColour(item, wx.Colour(192,192,192))

    def onPopupCopy(self, event):
        """ Copy the files to the clipboard """
        self.clipboard['files'] = self.getSelectedPaths()
        self.clipboard['delete'] = False
        
    def onPopupPaste(self, event):
        """ Paste the files to the selected directory """
        try: self.GetParent().StartBusy()
        except: pass

        dest = self.getSelectedPaths()[0]
        if not os.path.isdir(dest):
            dest = os.path.dirname(dest)
            
        def run(dest):
            delete = self.clipboard['delete']
            self.clipboard['delete'] = False
            newclipboard = []
            for i, file in enumerate(self.clipboard['files']):
                try:
                    newpath = os.path.join(dest, os.path.basename(file))
                    newclipboard.append(newpath)
                    if delete:
                        shutil.move(file, newpath)
                    else:
                        if os.path.isdir(file):
                            shutil.copytree(file, newpath, True)
                        else:
                            shutil.copy2(file, newpath)
                except (OSError, IOError), msg:
                    newclipboard.pop()
                    newclipboard.append(file)
                    # Do we have more files to copy/move?
                    if i < (len(self.clipboard['files'])-1):
                        rc = wx.MessageDialog(self, 
                          _('The system returned the following message when ' \
                            'attempting to move/copy %s: %s. ' \
                            'Do you wish to continue?' % (path, msg)), 
                          _('Error occurred when copying/moving files'), 
                          style=wx.YES_NO|wx.YES_DEFAULT|wx.ICON_ERROR).ShowModal()
                        if rc == wx.ID_NO:
                            break 
                    else:
                        rc = wx.MessageDialog(self, 
                          _('The system returned the following message when ' \
                            'attempting to move/copy %s: %s.' % (path, msg)), 
                          _('Error occurred when copying/moving files'), 
                          style=wx.OK|wx.ICON_ERROR).ShowModal()
            self.clipboard['files'] = newclipboard

        wx.lib.delayedresult.startWorker(self.endPaste, run, wargs=(dest,))

    def onPopupSCRefresh(self, event):
        self.scStatus(self.getSelectedNodes())

    def onPopupSCUpdate(self, event):
        self.scUpdate(self.getSelectedNodes())

    def onPopupSCHistory(self, event):
        self.scHistory(self.getSelectedNodes())

    def onPopupSCCommit(self, event):
        self.scCommit(self.getSelectedNodes())

    def onPopupSCRemove(self, event):
        self.scRemove(self.getSelectedNodes())

    def onPopupSCRevert(self, event):
        self.scRevert(self.getSelectedNodes())

    def onPopupSCAdd(self, event):
        self.scAdd(self.getSelectedNodes())

    def onPopupDelete(self, event):
        """ Delete selected files/directories """            
        projects = self.getChildren(self.root)
        selections = [(x, self.tree.GetPyData(x)['path']) 
                      for x in self.getSelectedNodes()]
 
        def delete():
            # Delete previously cut files
            for node, path in selections:
                try: 
                    Trash.moveToTrash(path)
                except Exception, msg:
                    rc = wx.MessageDialog(self, 
                      _('An error occurred when attempting to remove ') + msg[1] + 
                      _('. Do you wish to continue?'), 
                      _('Error occurred when removing files'), 
                      style=wx.YES_NO|wx.YES_DEFAULT|wx.ICON_ERROR).ShowModal()
                    if rc == wx.ID_NO:
                        break 
                    continue
                # If node is a project, remove it
                if node in projects:
                    self.tree.Collapse(node)
                    self.tree.Delete(node)
                    self.saveProjects()

        if selections:             
            threading.Thread(target=delete).start()

    def OnActivate(self, event):
        """
        Handles item activations events. (i.e double clicked or 
        enter is hit) and passes the clicked on file to be opened in 
        the notebook.

        """
        files = []
        for fname in self.getSelectedPaths():
            try:
                st = os.stat(fname)[0]
                if stat.S_ISREG(st) or stat.S_ISDIR(st) or stat.S_ISLNK(st):
                    files.append(fname)
            except (IOError, OSError): pass

        nb = wx.GetApp().GetMainWindow().nb

        for item in files:
            if nb.HasFileOpen(item):
                for page in xrange(nb.GetPageCount()):
                  ctrl = nb.GetPage(page)
                  if item == os.path.join(ctrl.dirname, ctrl.filename):
                      nb.SetSelection(page)
                      nb.ChangePage(page)
                      break
            else:
                nb.OnDrop([item])

    def watchDirectory(self, path, data=None, flag=True, delay=2):
        """
        Watch a directory for changes
    
        Required Arguments:
        path -- the path to watch
        func -- callback function with four arguments for added, modified,
            and deleted files and the data passed in
        data -- arbitrary data that will be passed to `func`
        flag -- if flag evaluates to false, the function should exit
        delay -- number of seconds between each poll
    
        """
        def getMTime(path):
            """ Get last modified times of all items in path """
            fileinfo = {}
            try: 
                for item in os.listdir(path):
                    try: fileinfo[item] = os.stat(os.path.join(path,item))[stat.ST_MTIME]
                    except OSError: pass
            except OSError: pass        
            return fileinfo
        
        # Continuously compare directory listings for 
        delay = max(1, int(delay))
        old = getMTime(path)
        while True:
            if not flag:
                return
            modified, added = [], []
            new = getMTime(path)
            for key, mtime in new.items():
                if key not in old:
                    added.append(key)
                else:
                    if mtime > old[key]:
                         modified.append(key)
                    del old[key]
            deleted = old.keys()

            # Set file list up for next pass
            old = new
            
            # Do callback if something changed
            if added or modified or deleted:
                evt = SyncNodesEvent(ppEVT_SYNC_NODES, self.GetId(), 
                                       (added, modified, deleted, data))
                wx.PostEvent(self, evt)
            
            # Check for the kill signal every second until the delay is finished
            for i in range(delay):
                if not flag:
                    return
                time.sleep(1)
        
    def __del__(self):
        """ Clean up resources """
        # Kill all watcher threads
        for value in self.watchers.values():
            value.pop()
            
        # Stop any currently running source control threads
        for t in self.scThreads:
            t._Thread__stop()
        
        # Clean up tempdir
        if self.tempdir:
            shutil.rmtree(self.tempdir, ignore_errors=True)
        diffwin.CleanupTempFiles()
            
class ProjectPane(wx.Panel):
    """Creates a project pane"""
    ID_REMOVE_PROJECT = wx.NewId()
    ID_ADD_PROJECT = wx.NewId()
    ID_CONFIG = wx.NewId()
    ID_CFGDLG = wx.NewId()

    def __init__(self, parent, id=ID_PROJECTPANE, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.NO_BORDER):
        wx.Panel.__init__(self, parent, id, pos, size, style)
        
        # Attributes
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.timer = wx.Timer(self)
        self.isBusy = 0

        self.projects = ProjectTree(self, None)

        # Layout Panes
        self.buttonbox = wx.BoxSizer(wx.HORIZONTAL)
        addbutton = wx.BitmapButton(self, self.ID_ADD_PROJECT, 
                                    self.projects.il.GetBitmap(self.projects.icons['project-add']), 
                                    size=(16,16), style=wx.NO_BORDER)
        addbutton.SetToolTip(wx.ToolTip(_("Add Project")))
        removebutton = wx.BitmapButton(self, self.ID_REMOVE_PROJECT, 
                                       self.projects.il.GetBitmap(self.projects.icons['project-delete']), 
                                       size=(16,16), style=wx.NO_BORDER)
        removebutton.SetToolTip(wx.ToolTip(_("Remove Project")))
        try:
            import ed_glob
            cfgbmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_PREF), wx.ART_MENU)
        except ImportError:
            cfgbmp = wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE, wx.ART_MENU)
        configbutton = wx.BitmapButton(self, self.ID_CONFIG, cfgbmp,
                                       size=(16,16), style=wx.NO_BORDER)
        configbutton.SetToolTip(wx.ToolTip(_("Configure")))
        self.busy = wx.Gauge(self, size=(50, 16), style=wx.GA_HORIZONTAL)
        self.busy.Hide()
        self.buttonbox.Add((10,24))
        self.buttonbox.Add(addbutton, 0, wx.ALIGN_CENTER_VERTICAL)
        self.buttonbox.Add((12,1))
        self.buttonbox.Add(removebutton, 0, wx.ALIGN_CENTER_VERTICAL)
        self.buttonbox.Add((12, 1))
        self.buttonbox.Add(configbutton, 0, wx.ALIGN_CENTER_VERTICAL)
        self.buttonbox.AddStretchSpacer()
        sizer.Add(self.buttonbox, 0, wx.EXPAND)

        sizer.Add(self.projects, 1, wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)

        # Event Handlers
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_BUTTON, self.OnPress)
        self.Bind(wx.EVT_TIMER, self.OnTick)
        self.Bind(cfgdlg.EVT_CFG_EXIT, self.OnCfgClose)

    def __del__(self):
        """Make sure the timer is stopped"""
        if self.timer.IsRunning():
            self.timer.Stop()

    def OnCfgClose(self, evt):
        """Recieve configuration data when dialog is closed"""
        e_id = evt.GetId()
        if e_id == self.ID_CFGDLG:
            val = evt.GetValue()
            if 'filters' in val:
                self.projects.filters = sorted(re.split(r'\s+', val['filters']))
            if 'diff' in val:
                self.projects.commands['diff'] = val['diff']
            if 'use_default_diff' in val:
                self.projects.useBuiltinDiff = val['use_default_diff']
            if 'syncwithnotebook' in val:
                self.projects.syncWithNotebook = val['syncwithnotebook']
            for key, value in self.projects.sourceControl.items():
                if key in val:
                    self.projects.sourceControl[key].command = val[key]
                    self.projects.sourceControl[key].filters = self.projects.filters
            self.projects.saveSettings()
            print "CONFIG DATA = ", val
        else:
            evt.Skip()

    def OnPaint(self, evt):
        """Paint the button area of the panel with a gradient"""
        if not util:
            evt.Skip()
            return
            
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)

        # Get some system colors
        col1 = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)
        col2 = util.AdjustColour(col1, 50)
        col1 = util.AdjustColour(col1, -50)

        rect = self.GetRect()
        grad = gc.CreateLinearGradientBrush(0, 1, 0, self.buttonbox.GetSize()[1], col2, col1)
        gc.SetBrush(grad)

        # Create the background path
        path = gc.CreatePath()
        path.AddRectangle(0, 0, rect.width - 0.5, rect.height - 0.5)

        gc.SetPen(wx.Pen(util.AdjustColour(col1, -60), 1))
        gc.DrawPath(path)

        evt.Skip()

    def OnPress(self, evt):
        """ Add/Remove projects """
        e_id = evt.GetId()
        if e_id == self.ID_ADD_PROJECT:
            dialog = wx.DirDialog(self, _('Choose a Project Directory'))
            if dialog.ShowModal() == wx.ID_OK:
                self.projects.addProject(dialog.GetPath())
        elif e_id == self.ID_REMOVE_PROJECT:
            self.projects.removeSelectedProject()
        elif e_id == self.ID_CONFIG:
            data = {}
            for key, value in self.projects.sourceControl.items():
                data[str(key)] = value.command
            data['filters'] = ' '.join(self.projects.filters)
            data['syncwithnotebook'] = self.projects.syncWithNotebook
            data['use_default_diff'] = self.projects.useBuiltinDiff
            for key, value in self.projects.commands.items():
                data[str(key)] = value
            if not self.FindWindowById(self.ID_CFGDLG):
                cfg = cfgdlg.ConfigDlg(self, self.ID_CFGDLG, 
                             cfgdlg.ConfigData(**data))
                cfg.Show()
            else:
                pass
        else:
            evt.Skip()

    def OnTick(self, evt):
        """Pulse the indicator on every tick of the clock"""
        self.busy.Pulse()

    def StartBusy(self):
        """Show and start the busy indicator"""
        self.isBusy += 1
        if self.isBusy > 1:
            return
        running = False
        for item in self.buttonbox.GetChildren():
            win = item.GetWindow()
            if isinstance(win, wx.Gauge):
                running = True
                break
        if not running:
            self.buttonbox.Add(self.busy, 1, 
                               wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
            self.buttonbox.Add((10, 24), 0, wx.ALIGN_RIGHT)

        self.busy.Show()
        self.buttonbox.Layout()
        self.timer.Start(100)

    def StopBusy(self):
        """Stop and then hide the busy indicator"""
        self.isBusy -= 1
        if self.isBusy > 0:
            return
        if self.timer.IsRunning():
            self.timer.Stop()
        self.busy.SetValue(0)
        wx.CallLater(1200, self.busy.Hide)

#-----------------------------------------------------------------------------#
class CommitDialog(wx.Dialog):
    """Dialog for entering commit messages"""
    def __init__(self, parent, title=u'', caption=u'', default=list()):
        """Create the Commit Dialog
        @keyword default: list of file names that are being commited

        """
        wx.Dialog.__init__(self, parent, title=title)
        
        # Attributes
        self._caption = wx.StaticText(self, label=caption)
        self._commit = wx.Button(self, wx.ID_OK, _("Commit"))
        self._commit.SetDefault()
        self._cancel = wx.Button(self, wx.ID_CANCEL)
        self._entry = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.NO_BORDER)
        if wx.Platform == '__WXMAC__':
            self._entry.MacCheckSpelling(True)
        self._DefaultMessage(default)
        self._entry.SetFocus()
        
        # Layout
        self._DoLayout()
        self.CenterOnParent()

    def _DefaultMessage(self, files):
        """
        Put the default message in the dialog and the given list of files

        """
        msg = list()
        msg.append(u':' + (u'-' * 35))
        msg.append(u": Lines beginning with `:' are removed automatically")
        msg.append(u": Modified Files:")
        for path in files:
            tmp = ":\t%s" % path
            msg.append(tmp)
        msg.append(u': ' + (u'-' * 30))
        msg.extend([u'', u''])
        msg = os.linesep.join(msg)
        self._entry.SetValue(msg)
        self._entry.SetInsertionPoint(len(msg))

    def _DoLayout(self):
        sizer = wx.GridBagSizer(5, 5)

        sizer.Add((5, 5), (0, 0))
        sizer.AddMany([(self._caption, (1, 1), (1, 4)),
                       (self._entry, (2, 1), (10, 8), wx.EXPAND),
                       (self._cancel, (12, 7)), (self._commit, (12, 8)),
                       ((5, 5), (13, 0)), ((5, 5), (13, 9))])
        self.SetSizer(sizer)
        self.SetInitialSize()

    def GetValue(self):
        """Return the value of the commit message"""
        msg = list()
        for line in xrange(self._entry.GetNumberOfLines()):
            tmp = self._entry.GetLineText(line)
            if tmp.strip().startswith(u':'):
                continue
            msg.append(tmp)
        return os.linesep.join(msg).strip()

class ExecuteCommandDialog(wx.Dialog):

    def __init__(self, parent, id):
        wx.Dialog.__init__(self, parent, id, _('Execute command on files'))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(self, -1, 
            _('Enter a command to be executed on all selected files ' \
              'and files in selected directories.')))

        sizer.Add(hsizer)
        sizer.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL), wx.ALIGN_RIGHT)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)


#-----------------------------------------------------------------------------#
if __name__ == '__main__':
        
    class MyApp(wx.App):
        def OnInit(self):
            frame = wx.Frame(None, -1, "Hello from wxPython")
            ProjectPane(frame)
            frame.Show(True)
            self.SetTopWindow(frame)
            return True

    app = MyApp(0)
    app.MainLoop()

