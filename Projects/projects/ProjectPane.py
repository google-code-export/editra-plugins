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
try: 
    import util         # from Editra.src
except ImportError: 
    util = None
import cfgdlg
from CVS import CVS
from SVN import SVN

# Make sure that all processes use a standard shell
if wx.Platform != '__WXMAC__':
    os.environ['SHELL'] = '/bin/sh'

# Configure Platform specific commands
if wx.Platform == '__WXMAC__': # MAC
    FILEMAN = 'Finder'
    FILEMAN_CMD = 'open'
elif wx.Platform == '__WXMSW__': # Windows
    FILEMAN = 'Explorer'
    FILEMAN_CMD = 'explorer'
else: # Other/Linux
    # TODO how to check what desktop environment is in use
    # this will work for Gnome but not KDE
    FILEMAN = 'Nautilus'
    FILEMAN_CMD = 'nautilus'
    #FILEMAN = 'Konqueror'
    #FILEMAN_CMD = 'konqueror'
    
# i18n support
_ = wx.GetTranslation

ID_PROJECTPANE = wx.NewId()
ID_PROJECTTREE = wx.NewId()

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

        self.tree = MyTreeCtrl(self, tID, wx.DefaultPosition, wx.DefaultSize,
                               wx.TR_DEFAULT_STYLE
                               #wx.TR_HAS_BUTTONS
                               | wx.TR_EDIT_LABELS
                               | wx.TR_MULTIPLE
                               | wx.TR_HIDE_ROOT
                               , self.log)

        icons = self.icons = {}
        menuicons = self.menuicons = {}

        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])

        try:
            import ed_glob
            icons['folder'] = il.Add(wx.ArtProvider.GetBitmap(str(ed_glob.ID_FOLDER), wx.ART_MENU))
            icons['folder-open'] = il.Add(wx.ArtProvider.GetBitmap(str(ed_glob.ID_OPEN), wx.ART_MENU))
            menuicons['copy'] = wx.ArtProvider.GetBitmap(str(ed_glob.ID_COPY), wx.ART_MENU)
            menuicons['cut'] = wx.ArtProvider.GetBitmap(str(ed_glob.ID_CUT), wx.ART_MENU)
            menuicons['paste'] = wx.ArtProvider.GetBitmap(str(ed_glob.ID_PASTE), wx.ART_MENU)
            menuicons['delete'] = wx.ArtProvider.GetBitmap(str(ed_glob.ID_DELETE), wx.ART_MENU)

        except ImportError:
            icons['folder'] = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, isz))
            icons['folder-open'] = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, isz))
            menuicons['copy'] = wx.ArtProvider_GetBitmap(wx.ART_COPY, wx.ART_OTHER, isz)
            menuicons['cut'] = wx.ArtProvider_GetBitmap(wx.ART_CUT, wx.ART_OTHER, isz)
            menuicons['paste'] = wx.ArtProvider_GetBitmap(wx.ART_PASTE, wx.ART_OTHER, isz)
            menuicons['delete'] = wx.ArtProvider_GetBitmap(wx.ART_DELETE, wx.ART_OTHER, isz)

        menuicons['blank'] = FileIcons.getBlankBitmap()
        menuicons['sc-commit'] = FileIcons.getScCommitBitmap()
        menuicons['sc-diff'] = FileIcons.getScDiffBitmap()
        menuicons['sc-history'] = FileIcons.getScHistoryBitmap()
        menuicons['sc-remove'] = FileIcons.getScRemoveBitmap()
        menuicons['sc-status'] = FileIcons.getScStatusBitmap()
        menuicons['sc-update'] = FileIcons.getScUpdateBitmap()
        menuicons['sc-revert'] = FileIcons.getScRevertBitmap()

        icons['file'] = il.Add(FileIcons.getFileBitmap())
        icons['file-uptodate'] = il.Add(FileIcons.getFileUptodateBitmap())
        icons['file-modified'] = il.Add(FileIcons.getFileModifiedBitmap())
        icons['file-conflict'] = il.Add(FileIcons.getFileConflictBitmap())
        icons['file-added'] = il.Add(FileIcons.getFileAddedBitmap())
        icons['project-add'] = il.Add(FileIcons.getProjectAddBitmap())
        icons['project-delete'] = il.Add(FileIcons.getProjectDeleteBitmap())

        self.tree.SetImageList(il)
        self.il = il
        
        self.filters = sorted(['CVS','dntnd','.DS_Store','.dpp','.newpp','*~',
                        '*.a','*.o','.poem','.dll','._*','.localized',
                        '.svn','*.pyc','*.bak','#*','*.pyo','*%*',
                        '*.previous','*.swp','.#*'])
        self.commands = {
            'diff': 'opendiff',
        }                
        self.syncWithNotebook = True
        self.sourceControl = {'cvs': CVS(), 'svn': SVN()}
        for key, value in self.sourceControl.items():
            value.filters = self.filters
                        
        self.watchers = {}
        self.clipboard = {}
        
        self.root = self.tree.AddRoot('Projects')
        self.tree.SetPyData(self.root, None)
        self.tree.SetItemImage(self.root, self.icons['folder'], wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root, self.icons['folder-open'], wx.TreeItemIcon_Expanded)

        self.loadSettings()

        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.OnItemExpanded, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.OnItemCollapsed, self.tree)
        #self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, self.tree)
        #self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginEdit, self.tree)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndEdit, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivate, self.tree)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
        try:
            import extern.flatnotebook as fnb
            #self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGING,
            mw = self.GetGrandParent()
            mw.nb.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.OnPageChanged)#, self.tree)
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

    def saveSettings(self):
        self.saveProjects()
        self.saveFilters()
        self.saveCommands()
        self.saveSourceControl()
        self.saveSyncWithNotebook()

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

    def syncNode(self, added, modified, deleted, parent):
        """
        Synchronize the tree nodes with the file system changes
        
        Required Arguments:
        added -- files that were added
        modified -- files that were modified
        deleted -- files that were deleted
        parent -- tree node corresponding to the directory
        
        """            
        children = {}
        for child in self.getChildren(parent):
            children[self.tree.GetItemText(child)] = child
            
        if children:
            for item in deleted:
                if item in children:
                    self.tree.Delete(children[item])

        for item in added:
            if os.path.basename(item) not in children:
                self.addPath(parent, item)

        self.tree.SortChildren(parent)

    def getSelectedNodes(self):
        return self.tree.GetSelections()
                        
    def getSelectedPaths(self):
        """ Get paths associated with selected items """
        paths = []
        for item in self.getSelectedNodes():
            paths.append(self.tree.GetPyData(item)['path'])
        return paths
        
    def OnPageChanged(self, evt):
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

        # Very important this must be called in the handler at some point
        evt.Skip()
    
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
        # Make sure that the directory is under source control
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

    def scCommand(self, nodes, command, **options):
        """
        Run a source control command 
        
        Required Arguments:
        nodes -- selected tree nodes
        command -- name of command type to run
        
        """
        for node in nodes:
            #print command
            data = self.tree.GetPyData(node)
            if data.get('sclock', None):
                return
            
            sc = self.getSCSystem(data['path'])
            if sc is None:
                return
                
            data['sclock'] = True 

            def run(node, data, sc):
                method = getattr(sc, command, None)
                if method:
                    # Run command
                    method([data['path']], **options)
                
                    # Unlock
                    del data['sclock']
                
                    # Update status
                    self.scStatus([node])

            t = threading.Thread(target=run, args=(node, data, sc))
            t.setDaemon(True)
            t.start()    
            t.join(60)
        
    def scCommit(self, nodes, **options): 
        while True:      
            ted = CommitDialog(self, _("Commit Dialog"), 
                               _("Enter your commit message:"))
            if ted.ShowModal() != wx.ID_OK:
                return
            message = ted.GetValue().strip().replace('"', '\\"')
            if message:
                break
        self.scCommand(nodes, 'commit', message=message)
       
    def scStatus(self, nodes):
        """
        Update the CVS/SVN status of the files in the given node

        Required Arguments:
        node -- tree node of items to get the status of

        """
        for node in nodes:
            data = self.tree.GetPyData(node)
            if data.get('sclock', None):
                return
                
            sc = self.getSCSystem(data['path'])
            if sc is None:
                return
                
            data['sclock'] = True 
            
            def update(node, data, sc):
                time.sleep(0.2)
                try:
                    status = sc.status([data['path']])
                    # Update the icons for the file nodes
                    if os.path.isdir(data['path']):
                        for child in self.getChildren(node):
                            text = self.tree.GetItemText(child)
                            if text not in status:
                                continue
                            icon = self.icons.get('file-'+status[text]['status'])
                            if icon and not os.path.isdir(os.path.join(data['path'],text)):
                                self.tree.SetItemImage(child, icon,
                                                       wx.TreeItemIcon_Normal)
                    else:
                        text = self.tree.GetItemText(node)
                        if text in status:
                            icon = self.icons.get('file-'+status[text]['status'])
                            if icon:
                                self.tree.SetItemImage(node, icon,
                                     wx.TreeItemIcon_Normal)
                except (OSError, IOError):
                    raise
                del data['sclock']

            t = threading.Thread(target=update, args=(node,data,sc))
            t.setDaemon(True)
            t.start()
            t.join(60)

    def diffToPrevious(self, node):
        """ Use opendiff to compare playpen version to repository version """
        def diff():
            path = self.tree.GetPyData(node)['path']
            # Only do files
            if os.path.isdir(path):
                for child in self.getChildren(node):
                    self.diffToPrevious(child)
                return

            sc = self.getSCSystem(path)
            if sc is None:
                return

            content = sc.fetch([path])
            if content and content[0] is None:
                return wx.MessageDialog(self, 
                                        'The requested file could not be ' +
                                        'retrieved from the source control system.', 
                                        'Could not retrieve file', 
                                        style=wx.OK|wx.ICON_ERROR).ShowModal()
                                        
            open('%s.previous' % path, 'w').write(content[0])
            subprocess.call([self.commands['diff'], '%s.previous' % path, path]) 
            time.sleep(3)
            os.remove('%s.previous' % path)
            
        t = threading.Thread(target=diff)
        t.setDaemon(True)
        t.start()

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
                                               args=(path, self.syncNode), 
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
        parentpath = self.tree.GetPyData(parent)['path']
        itempath = os.path.join(parentpath,name)
        if os.path.isfile(itempath):
            return self.addFile(parent, name)
        elif os.path.isdir(itempath):
            return self.addFolder(parent, name)

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

        # make a menu
        menu = wx.Menu()
        items = [
            (self.popupIDEdit, _('Edit'), None, True),
            (self.popupIDOpen, _('Open'), None, True),
            (self.popupIDReveal, _("Reveal in %s" % FILEMAN), None, True),
            (None, None, None, None),
            (self.popupIDCut, _('Cut'), 'cut', True),
            (self.popupIDCopy, _('Copy'), 'copy', True),
            (self.popupIDPaste, _('Paste'), 'paste', True),
            (None, None, None, None),
            #(self.popupIDRename, _('Rename'), None, True),
            #(None, None, None, None),
            (self.popupIDSCRefresh, _("Refresh status"), 'sc-status', True),
            (self.popupIDSCUpdate, _("Update"), 'sc-update', True),
            (self.popupIDSCDiff, _("Compare to previous version"), 'sc-diff', True),
            (self.popupIDSCHistory, _("Show revision history"), 'sc-history', False),
            (self.popupIDSCCommit, _("Commit changes"), 'sc-commit', True),
            (self.popupIDSCRemove, _("Remove from repository"), 'sc-remove', True),
            (self.popupIDSCRevert, _("Revert to repository version"), 'sc-revert', True),
            (self.popupIDSCAdd, _("Add to repository"), None, True),
            (None, None, None, None),
            (self.popupIDDelete, _("Delete"), 'delete', True),
        ]
        for id, title, icon, enabled in items:
            if id is None:
                menu.AppendSeparator()
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

    def onPopupEdit(self, event):
        """ Open the current file in the editor """
        return self.OnActivate(event)

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
            self.diffToPrevious(node)
            
    def _clearClipboard(self):
        """ Remove any previously cut files/directories """
        cutfiles = self.clipboard.pop('cut-files', [])
        self.clipboard.pop('copied-files', None)
 
        def delete():
            # Delete previously cut files
            for path in cutfiles:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    try: os.remove(path)
                    except OSError: pass
       
        if cutfiles:             
            threading.Thread(target=delete).start()

    def onPopupCut(self, event):
        """ Cut the files to the clipboard """
        self._clearClipboard()
        # Cut selected files
        self.clipboard['cut-files'] = []
        for path in self.getSelectedPaths():
            dirname, basename = os.path.split(path)
            newpath = os.path.join(dirname, '.'+basename+'\r')
            os.rename(path, newpath)
            self.clipboard['cut-files'].append(newpath)

    def onPopupCopy(self, event):
        """ Copy the files to the clipboard """
        self._clearClipboard() 
        self.clipboard['copied-files'] = self.getSelectedPaths()
        
    def onPopupPaste(self, event):
        """ Paste the files to the selected directory """
        dest = self.getSelectedPaths()[0]
        if not os.path.isdir(dest):
            dest = os.path.dirname(dest)
        for file in self.clipboard.get('copied-files', []):
            newpath = os.path.join(dest, os.path.basename(file))
            if os.path.isdir(file):
                shutil.copytree(file, newpath, True)
            else:
                shutil.copy2(file, newpath)
        for file in self.clipboard.get('cut-files', []):
            # Remove '.' and '\r' from file before copying
            newpath = os.path.join(dest, os.path.basename(file)[1:-1])
            if os.path.isdir(file):
                shutil.copytree(file, newpath, True)
            else:
                shutil.copy2(file, newpath)

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
        rc = wx.MessageDialog(self, 
                              _('This operation will permanently delete selected ' \
                              'files and directories.  Are you sure you want to continue?'), 
                              _('Permanently delete files and directories?'), 
                              style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_EXCLAMATION).ShowModal()
        if rc not in [wx.ID_OK, wx.ID_YES]:
            return 
            
        files = self.getSelectedPaths()
 
        def delete():
            # Delete previously cut files
            for path in files:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    try: os.remove(path)
                    except OSError: pass
        if files:             
            threading.Thread(target=delete).start()

    def OnActivate(self, event):
        """
        Handles item activations events. (i.e double clicked or 
        enter is hit) and passes the clicked on file to be opened in 
        the notebook.

        """
        files = self.getSelectedPaths()
        to_open = list()
        for fname in files:
            try:
                st = os.stat(fname)[0]
                if stat.S_ISREG(st) or stat.S_ISDIR(st) or stat.S_ISLNK:
                    to_open.append(fname)
            except:
                pass
        wx.GetApp().GetMainWindow().nb.OnDrop(to_open)

    def watchDirectory(self, path, func, data=None, flag=True, delay=2):
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
                func(added, modified, deleted, data)
            
            # Check for the kill signal every second until the delay is finished
            for i in range(delay):
                if not flag:
                    return
                time.sleep(1)
        
    def __del__(self):
        # Kill all watcher threads
        for value in self.watchers.values():
            value.pop()
        # Remove any temp files
        self._clearClipboard()
    
            
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
        self.buttonbox.Add((10,24))
        self.buttonbox.Add(addbutton, 0, wx.ALIGN_CENTER_VERTICAL)
        self.buttonbox.Add((12,1))
        self.buttonbox.Add(removebutton, 0, wx.ALIGN_CENTER_VERTICAL)
        self.buttonbox.Add((12, 1))
        self.buttonbox.Add(configbutton, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.buttonbox, 0)

        sizer.Add(self.projects, 1, wx.EXPAND)

        self.SetSizer(sizer)

        # Event Handlers
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_BUTTON, self.OnPress)
        self.Bind(cfgdlg.EVT_CFG_EXIT, self.OnCfgClose)

    def OnCfgClose(self, evt):
        """Recieve configuration data when dialog is closed"""
        e_id = evt.GetId()
        if e_id == self.ID_CFGDLG:
            val = evt.GetValue()
            if 'filters' in val:
                self.projects.filters = sorted(re.split(r'\s+', val['filters']))
            if 'diff' in val:
                self.projects.commands['diff'] = val['diff']
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
                data[key] = value.command
            data['filters'] = ' '.join(self.projects.filters)
            data['syncwithnotebook'] = self.projects.syncWithNotebook
            for key, value in self.projects.commands.items():
                data[key] = value
            if not self.FindWindowById(self.ID_CFGDLG):
                cfg = cfgdlg.ConfigDlg(self, self.ID_CFGDLG, 
                             cfgdlg.ConfigData(**data))
                cfg.Show()
            else:
                pass
        else:
            evt.Skip()

#-----------------------------------------------------------------------------#
class CommitDialog(wx.Dialog):
    """Dialog for entering commit messages"""
    def __init__(self, parent, title=u'', caption=u'', default=u''):
        wx.Dialog.__init__(self, parent, title=title)
        
        # Attributes
        self._caption = wx.StaticText(self, label=caption)
        self._commit = wx.Button(self, wx.ID_OK, _("Commit"))
        self._commit.SetDefault()
        self._cancel = wx.Button(self, wx.ID_CANCEL)
        self._entry = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.NO_BORDER)
        self._entry.SetValue(default)
        self._entry.SetFocus()
        
        # Layout
        self._DoLayout()
        self.CenterOnParent()

    def _DoLayout(self):
        sizer = wx.GridBagSizer(5, 5)

        sizer.Add((5, 5), (0, 0))
        sizer.AddMany([(self._caption, (1, 1), (1, 4)),
                       (self._entry, (2, 1), (10, 6), wx.EXPAND),
                       (self._cancel, (12, 5)), (self._commit, (12, 6)),
                       ((5, 5), (13, 0)), ((5, 5), (13, 7))])
        self.SetSizer(sizer)
        self.SetInitialSize()

    def GetValue(self):
        """Return the value of the commit message"""
        return self._entry.GetValue()

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

