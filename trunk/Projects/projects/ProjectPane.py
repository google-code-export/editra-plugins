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

# Make sure that all processes use a standard shell
if wx.Platform != '__WXMAC__':
    os.environ['SHELL'] = '/bin/sh'

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
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.log = log
        tID = wx.NewId()

        self.tree = MyTreeCtrl(self, tID, wx.DefaultPosition, wx.DefaultSize,
                               wx.TR_DEFAULT_STYLE
                               #wx.TR_HAS_BUTTONS
                               #| wx.TR_EDIT_LABELS
                               #| wx.TR_MULTIPLE
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

        icons['file'] = il.Add(FileIcons.getFileBitmap())
        icons['file-uptodate'] = il.Add(FileIcons.getFileUptodateBitmap())
        icons['file-modified'] = il.Add(FileIcons.getFileModifiedBitmap())
        icons['file-merge'] = il.Add(FileIcons.getFileMergeBitmap())
        icons['project-add'] = il.Add(FileIcons.getProjectAddBitmap())
        icons['project-delete'] = il.Add(FileIcons.getProjectDeleteBitmap())

        self.tree.SetImageList(il)
        self.il = il
        
        self.filters = ['CVS','dntnd','.DS_Store','.dpp','.newpp','*~',
                        '*.a','*.o','.poem','.dll','._*','.localized',
                        '.svn','*.pyc','*.bak','#*','*.pyo','*%*',
                        '*.previous','*.swp']
        self.commands = {
            'cvs': 'cvs',
            'svn': 'svn',
            'diff': 'opendiff',
        }                
                        
        self.watchers = {}
        self.clipboard = {}
        
        self.root = self.tree.AddRoot('Projects')
        self.tree.SetPyData(self.root, None)
        self.tree.SetItemImage(self.root, self.icons['folder'], wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root, self.icons['folder-open'], wx.TreeItemIcon_Expanded)

        self.loadProjects()

        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.OnItemExpanded, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.OnItemCollapsed, self.tree)
        #self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, self.tree)
        #self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginEdit, self.tree)
        #self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndEdit, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivate, self.tree)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
        try:
            import extern.flatnotebook as fnb
            #self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGING,
            self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.OnPageChanged, self.tree)
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

    def loadProjects(self):
        """ Load projects from config file """
        for p in self.readConfig().get('projects',[]):
            self.addProject(p, save=False)

    def saveProjects(self):
        """ Save projects to config file """
        self.writeConfig(projects=self.getProjectPaths())

    def addProject(self, path, save=True):
        """
        Add a project for the given path
        
        Required Arguments:
        path -- full path to the project directory
        
        Returns: tree node for the project
        
        """
        node = self.tree.AppendItem(self.tree.GetRootItem(), os.path.basename(path))
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

    def OnPageChanged(self, event):
        print 'PAGE CHANGED'
        event.Skip()

    def OnRightDown(self, event):
        pt = event.GetPosition();
        item, flags = self.tree.HitTest(pt)
        if item:
            self.log.WriteText("OnRightClick: %s, %s, %s\n" %
                               (self.tree.GetItemText(item), type(item), item.__class__))
            self.tree.SelectItem(item)

    def OnRightUp(self, event):
        pt = event.GetPosition();
        item, flags = self.tree.HitTest(pt)
        if item:        
            self.log.WriteText("OnRightUp: %s (manually starting label edit)\n"
                               % self.tree.GetItemText(item))
            self.tree.EditLabel(item)

    def OnBeginEdit(self, event):
        self.log.WriteText("OnBeginEdit\n")
        # show how to prevent edit...
        item = event.GetItem()
        if item and self.tree.GetItemText(item) == "The Root Item":
            wx.Bell()
            self.log.WriteText("You can't edit this one...\n")

            # Lets just see what's visible of its children
            cookie = 0
            root = event.GetItem()
            (child, cookie) = self.tree.GetFirstChild(root)

            while child.IsOk():
                self.log.WriteText("Child [%s] visible = %d" %
                                   (self.tree.GetItemText(child),
                                    self.tree.IsVisible(child)))
                (child, cookie) = self.tree.GetNextChild(root, cookie)

            event.Veto()

    def OnEndEdit(self, event):
        self.log.WriteText("OnEndEdit: %s %s\n" %
                           (event.IsEditCancelled(), event.GetLabel()) )
        # show how to reject edit, we'll not allow any digits
        for x in event.GetLabel():
            if x in string.digits:
                self.log.WriteText("You can't enter digits...\n")
                event.Veto()
                return

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
        self.tree.SortChildren(parent)
        self.addDirectoryWatcher(parent)        
        self.scStatus(parent)

    def diffToPrevious(self, node):
        """ Use opendiff to compare playpen version to repository version """
        def diff():
            path = self.tree.GetPyData(node)['path']
            # Only do files
            if os.path.isdir(path):
                return
            filename = os.path.basename(path)
            type = self.getSCType(node)
            if type == 'cvs':
                #print os.path.dirname(path), os.path.basename(path)
                content = os.popen('cd "%s" && %s checkout -p %s' % 
                                    (os.path.dirname(path),
                                     self.commands['cvs'],
                                     os.path.basename(path))).read()
            elif type == 'svn':
                content = os.popen('cd "%s" && %s cat %s' % 
                                    (os.path.dirname(path),
                                     self.commands['svn'],
                                     os.path.basename(path))).read()
            if not content.strip():
                return wx.MessageDialog(self, 'The requested file could not be retrieved from the source control system.', 
                                        'Could not retrieve file', 
                                        style=wx.OK|wx.ICON_ERROR).ShowModal()
            open('%s.previous' % path, 'w').write(content)
            subprocess.call([self.commands['diff'], '%s.previous' % path, path]) 
            time.sleep(3)
            os.remove('%s.previous' % path)
        t = threading.Thread(target=diff)
        t.setDaemon(True)
        t.start()

    def getSCType(self, node):
        """ Get the version control system used for the given node """
        if self.isCVSControlled(node):
            return 'cvs'
        elif self.isSVNControlled(node):
            return 'svn'

    def scCommand(self, node, command, **options):
        """
        Run a SC command 
        
        Required Arguments:
        node -- selected tree node
        command -- name of command type to run
        
        """
        data = self.tree.GetPyData(node)
        if data.get('sclock', None):
            return
            
        sctype = self.getSCType(node)
        if not sctype:
            return
            
        data['sclock'] = True 

        def run():
            method = getattr(self, sctype+command.title(), None)
            if method:
                # Run command
                method(data['path'], **options)
            
                # Unlock
                del data['sclock']
            
                # Update status
                self.scStatus(node)

        t = threading.Thread(target=run)
        t.setDaemon(True)
        t.start()    
        
    def scRevert(self, node):
        return self.scCommand(node, 'revert')

    def cvsRevert(self, path):
        """
        NOTE: This method is not recursive, it only reverts files in the
              current node.
        """
        for file in self.cvsStatus(path):
            os.system('cd "%s" && %s checkout -p %s > %s' % \
                       (path, self.commands['cvs'], file, file))

    def svnRevert(self, path):
        filename = '.'
        if not os.path.isdir(path):
            path, filename = os.path.split(path)
        # Go to the directory and run svn update
        os.system('cd "%"s && %s revert -R %s' % \
                   (path, self.commands['svn'], filename))

    def scCommit(self, node, **options): 
        while True:      
            ted = wx.TextEntryDialog(self, 
                     'This text will be used as the message text for the commit',
                     'Please enter commit message')
            if ted.ShowModal() != wx.ID_OK:
                return
            message = ted.GetValue().strip().replace('"', '\\"')
            if message:
                break
        return self.scCommand(node, 'commit', message=message)
       
    def cvsCommit(self, path, message=None):
        filename = ''
        if not os.path.isdir(path):
            path, filename = os.path.split(path)
        root = open(os.path.join(path,'CVS','Root')).read().strip()
        # Go to the directory and run cvs commit
        os.system('cd "%s" && %s -d%s commit -R -m "%s" %s' % 
                   (path, self.commands['cvs'], message, root, filename))
        
    def svnCommit(self, path, message=None):
        filename = ''
        if not os.path.isdir(path):
            path, filename = os.path.split(path)        
        # Go to the directory and run svn commit
        os.system('cd "%s" && %s commit -m "%s" %s' % \
                   (path, self.commands['svn'], message, filename))
    
    def scUpdate(self, node):
        return self.scCommand(node, 'update')
        
    def cvsUpdate(self, path):
        filename = ''
        if not os.path.isdir(path):
            path, filename = os.path.split(path)
        root = open(os.path.join(path,'CVS','Root')).read().strip()
        # Go to the directory and run cvs update
        os.system('cd "%s" && %s -d%s update -R %s' % 
                   (path, self.commands['cvs'], root, filename))
        
    def svnUpdate(self, path):
        filename = ''
        if not os.path.isdir(path):
            path, filename = os.path.split(path)        
        # Go to the directory and run svn update
        os.system('cd "%s" && %s update %s' % \
                   (path, self.commands['svn'], filename))

    def scStatus(self, node):
        """
        Update the CVS/SVN status of the files in the given node

        Required Arguments:
        node -- tree node of items to get the status of

        """
        data = self.tree.GetPyData(node)
        if data.get('sclock', None):
            return
            
        sctype = self.getSCType(node)
        if not sctype:
            return
            
        data['sclock'] = True 
        
        def update():
            time.sleep(0.1)
            try:
                if not hasattr(self, '%sStatus' % sctype):
                    return
                status = getattr(self, '%sStatus' % sctype)(data['path'])
                # Update the icons for the file nodes
                if os.path.isdir(data['path']):
                    for child in self.getChildren(node):
                        text = self.tree.GetItemText(child)
                        if text not in status:
                            continue
                        icon = self.icons.get('file-'+status[text])
                        if icon and not os.path.isdir(os.path.join(data['path'],text)):
                            self.tree.SetItemImage(child, icon,
                                                   wx.TreeItemIcon_Normal)
                else:
                    text = self.tree.GetItemText(node)
                    if text in status:
                        icon = self.icons.get('file-'+status[text])
                        if icon:
                            self.tree.SetItemImage(node, icon,
                                 wx.TreeItemIcon_Normal)
            except (OSError, IOError):
                pass
            del data['sclock']

        t = threading.Thread(target=update)
        t.setDaemon(True)
        t.start()

    def isCVSControlled(self, node):
        path = self.tree.GetPyData(node)['path']
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        return os.path.isdir(os.path.join(path,'CVS'))
        
    def isSVNControlled(self, node):
        path = self.tree.GetPyData(node)['path']
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        return os.path.isdir(os.path.join(path,'.svn'))
    
    def cvsStatus(self, path):
        """ Get CVS status information from given file/directory """
        status = {}
        status_re = re.compile(r'^File:\s+(\S+)\s+Status:\s+(.+?)\s*$')
        
        filename = ''
        if not os.path.isdir(path):
            path, filename = os.path.split(path)
        
        root = open(os.path.join(path,'CVS','Root')).read().strip()
        # Go to the directory and run cvs status
        for line in os.popen('cd "%s" && %s -d%s status -l %s' % \
                              (path, self.commands['cvs'], root, filename)):
            m = status_re.match(line) 
            if not m:
                continue
            status[m.group(1)] = m.group(2).replace('-','').split()[-1].lower()
        return status

    def svnStatus(self, path):
        """ Get SVN status information from given file/directory """
        status = {}
        codes = {' ':'uptodate', 'A':'added', 'C':'conflict', 'D':'deleted',
                 'M':'modified', 'R':'replaced', 'I':'ignored'}

        filename = ''
        if not os.path.isdir(path):
            path, filename = os.path.split(path)
        
        # Go to the directory and run svn status
        for line in os.popen('cd "%s" && %s -vN status %s' % \
                              (path, self.commands['svn'], filename)):
            name = line.strip().split()[-1]
            try: status[name] = codes[line[0]]
            except KeyError: pass
        return status

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

        # make a menu
        menu = wx.Menu()
        items = [
            (self.popupIDEdit, 'Edit', None, True),
            (self.popupIDOpen, 'Open', None, True),
            (self.popupIDReveal, 'Reveal in Finder', None, True),
            (None, None, None, None),
            (self.popupIDCut, 'Cut', 'cut', True),
            (self.popupIDCopy, 'Copy', 'copy', True),
            (self.popupIDPaste, 'Paste', 'paste', True),
            (None, None, None, None),
            (self.popupIDSCRefresh, "Refresh status", None, True),
            (self.popupIDSCUpdate, "Update", None, True),
            (self.popupIDSCDiff, "Compare to previous version", None, True),
            (self.popupIDSCHistory, "Show revision history", None, False),
            (self.popupIDSCCommit, "Commit changes", None, True),
            (self.popupIDSCRemove, "Remove from repository", None, False),
            (self.popupIDSCRevert, "Revert to repository version", None, True),
            (self.popupIDSCAdd, "Add to repository", None, False),
            (None, None, None, None),
            (self.popupIDDelete, "Delete", 'delete', True),
        ]
        for id, title, icon, enabled in items:
            if id is None:
                menu.AppendSeparator()
                continue
            item = wx.MenuItem(menu, id, title)
            if icon: 
                item.SetBitmap(self.menuicons[icon])
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
            subprocess.call(['open', file])

    def onPopupReveal(self, event):
        """ Open the Finder to the parent directory """
        for file in self.getSelectedPaths():
            subprocess.call(['open', os.path.dirname(file)])

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
        """ Refresh SC status for selected nodes """
        for node in self.getSelectedNodes():
            self.scStatus(node)

    def onPopupSCUpdate(self, event):
        for node in self.getSelectedNodes():
            self.scUpdate(node)

    def onPopupSCHistory(self, event):
        self.log.WriteText("Popup nine\n")

    def onPopupSCCommit(self, event):
        for node in self.getSelectedNodes():
            self.scCommit(node)

    def onPopupSCRemove(self, event):
        self.log.WriteText("Popup nine\n")

    def onPopupSCRevert(self, event):
        for node in self.getSelectedNodes():
            self.scRevert(node)

    def onPopupSCAdd(self, event):
        self.log.WriteText("Popup nine\n")

    def onPopupDelete(self, event):
        """ Delete selected files/directories """
        rc = wx.MessageDialog(self, 'This operation will permanently delete selected ' +
                              'files and directories.  Are you sure you want to continue?', 
                              'Permanently delete files and directories?', 
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

    def __init__(self, parent, id=ID_PROJECTPANE, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.NO_BORDER):
        wx.Panel.__init__(self, parent, id, pos, size, style)
        
        # Attributes
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.projects = ProjectTree(self, None)

        # Layout Panes
        buttonbox = wx.BoxSizer(wx.HORIZONTAL)
        addbutton = wx.BitmapButton(self, self.ID_ADD_PROJECT, self.projects.il.GetBitmap(self.projects.icons['project-add']), size=(16,16), style=wx.NO_BORDER)
        removebutton = wx.BitmapButton(self, self.ID_REMOVE_PROJECT, self.projects.il.GetBitmap(self.projects.icons['project-delete']), size=(16,16), style=wx.NO_BORDER)
        buttonbox.Add((10,30))
        buttonbox.Add(addbutton, 0, wx.ALIGN_CENTER_VERTICAL)
        buttonbox.Add((12,1))
        buttonbox.Add(removebutton, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(buttonbox, 0)

        sizer.Add(self.projects, 1, wx.EXPAND)

        self.SetSizer(sizer)

        # Event Handlers
        #self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_BUTTON, self.OnPress)

    def OnPress(self, evt):
        """ Add/Remove projects """
        e_id = evt.GetId()
        if e_id == self.ID_ADD_PROJECT:
            dialog = wx.DirDialog(self, 'Choose a Project Directory')
            if dialog.ShowModal() == wx.ID_OK:
                self.projects.addProject(dialog.GetPath())
        elif e_id == self.ID_REMOVE_PROJECT:
            self.projects.removeSelectedProject()
        else:
            evt.Skip()


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

