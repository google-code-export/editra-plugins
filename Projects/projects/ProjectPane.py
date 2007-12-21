#!/usr/bin/env python

"""
ProjectPane

The ProjectPane module creates a wx frame that handles file management
as well as source control.  The file management operations are similar
to those found in Windows Explorer and Apple's Finder.  You can cut, copy,
and paste files.  Create new files and directories.  And it even deletes
files to the Recycle Bin or Trash.

While the file management utilities are useful, the source control functions
are where the majority of the functionality of the ProjectPane lies.
Currently, the ProjectPane has support for CVS, GIT, and Subversion.  It 
is possible to create objects to handle other source control systems
as well (see SourceControl.py).  The ProjectPane uses a non-invasive approach
to handling source control.  It doesn't check files out or browse repositories,
it simply detects directories and files that are under source control and 
gives you access to the operations available to that system.  When properly
configured, files and folders under source control will display the status
of the file/folder as a badge on the icon.  The right-click menu gives you 
access to source control operations such as status updates, committing, 
removing, and reverting to the repository revision.

But it doesn't end there.  Probably the most powerful feature of the ProjectPane
is its diffing utitility and history window.  You can compare your copy
of a file to any previous revision using the history window.  You can also
compare any two repository revisions.  Locating revisions is easy using the
interactive search that filters the visible revisions based on the commit log
messages.

There are several configuration options that allow you to suit the ProjectPane
to your needs.  The general options are listed below:

    File Filters -- this is a space separated list of file globbing patterns
        that you can use to remove files from the tree view.  This is useful
        for eliminating backup files and intermediate build files that you
        won't be using in the editor.

    Editor Notebook Synchronization -- when a file in opened in the editor
        notebook, you can have the ProjectPane automatically show this file
        in the current projects by enabling this feature.

    Diff Program -- you can choose to use an internal visuall diffing program
        or specify an external command.

The source control options are even more extensive.  Each source control 
repository has its own set of options.  You can set authentication information
and environment variables for each repository.  It is also possible to use
partial repository paths.  All settings from partial or full repository path
matches will be applied.  The longer the match string, the higher the 
precedence. All settings in the Default section have the lowest priority, but 
are applied to all repositories.

"""

__author__ = "Kevin D. Smith <Kevin.Smith@sixquickrun.com>"
__revision__ = "$Revision$"
__scid__ = "$Id$"

import wx 
import os 
import time 
import threading 
import stat 
import fnmatch
import re 
import FileIcons
import subprocess
import shutil
import Trash
import wx.lib.delayedresult 
import diffwin

import ConfigDialog
from HistWin import AdjustColour

try:
    import profiler
    eol = profiler.Profile_Get('EOL')
    if 'Unix' in eol:
        eol = '\n'
    elif 'Windows' in eol:
        eol = '\r\n'
    else:
        eol = '\r'
except ImportError:
    profiler = None
    eol = '\n'

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

ODD_PROJECT_COLOR = wx.Colour(232, 239, 250)
EVEN_PROJECT_COLOR = wx.Colour(232, 239, 250)
ODD_BACKGROUND_COLOR = wx.Colour(255, 255, 255)
EVEN_BACKGROUND_COLOR = wx.Colour(255, 255, 255)

# i18n support
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

FILE_TYPES = {
    _('Text File'): {'ext':'.txt'},
    _('C File'): {'ext':'.c'},
    _('HTML File'): {'ext':'.html', 'template':'<html>\n<head><title></title></head>\n<body>\n\n</body>\n</html>'},
    _('Php File'): {'ext':'.php', 'template':'<?php\n\n?>'},
    _('Python File'): {'ext':'.py', 'template':'#!/usr/bin/env python\n\n'},
}
    
ID_PROJECTPANE = wx.NewId()
ID_PROJECTTREE = wx.NewId()

#-----------------------------------------------------------------------------#

class SimpleEvent(wx.PyCommandEvent):
    """Base event to signal that nodes need updating"""
    def __init__(self, etype, eid, value=None):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

    def GetValue(self):
        """Get the events value"""
        return self._value

ppEVT_SYNC_NODES = wx.NewEventType()
EVT_SYNC_NODES = wx.PyEventBinder(ppEVT_SYNC_NODES, 1)
class SyncNodesEvent(SimpleEvent):
    pass

ppEVT_UPDATE_STATUS = wx.NewEventType()
EVT_UPDATE_STATUS = wx.PyEventBinder(ppEVT_UPDATE_STATUS, 1)
class UpdateStatusEvent(SimpleEvent):
    pass

#-----------------------------------------------------------------------------#

class MyTreeCtrl(wx.TreeCtrl):

    def __init__(self, parent, id, pos, size, style, log):
        wx.TreeCtrl.__init__(self, parent, id, pos, size, style)
        self.log = log

    def OnCompareItems(self, item1, item2):
        """Compare the text of two tree items"""
        t1 = self.GetItemText(item1).lower()
        t2 = self.GetItemText(item2).lower()
        #self.log.WriteText('compare: ' + t1 + ' <> ' + t2 + '\n')
        if t1 < t2:
            return -1
        elif t1 == t2:
            return 0
        else:
            return 1

#-----------------------------------------------------------------------------#

class ProjectTree(wx.Panel):
    """ Tree control for holding project nodes """

    def __init__(self, parent, log):
        # Use the WANTS_CHARS style so the panel doesn't eat the Return key.
        wx.Panel.__init__(self, parent, -1, 
                          style=wx.WANTS_CHARS|wx.SUNKEN_BORDER)

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
                               | wx.TR_FULL_ROW_HIGHLIGHT
                               , self.log)

        # Load icons for use later
        icons = self.icons = {}
        menuicons = self.menuicons = {}

        isz = (16, 16)
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
        for badge in ['uptodate', 'modified', 'conflict', 'added', 'merge']:
            badgeicon = getattr(FileIcons, 'getBadge' + badge.title() + 'Bitmap')().ConvertToImage()
            badgeicon.Rescale(11, 11, wx.IMAGE_QUALITY_HIGH)
            for icotype in ['file', 'folder', 'folder-open']:
                icon = wx.MemoryDC()
                if icotype == 'file':
                    tbmp = FileIcons.getFileBitmap()
                elif icotype == 'folder':
                    tbmp = folder
                else:
                    tbmp = folderopen

                icon.SelectObject(tbmp)
                icon.SetBrush(wx.TRANSPARENT_BRUSH)
                if wx.Platform == '__WXGTK__':
                    x, y = 3, 4
                else:
                    x, y = 5, 5
                icon.DrawBitmap(wx.BitmapFromImage(badgeicon), x, y, False)
                icon.SelectObject(wx.NullBitmap)
                icons[icotype + '-' + badge] = il.Add(tbmp)

        icons['project-add'] = il.Add(FileIcons.getProjectAddBitmap())
        icons['project-delete'] = il.Add(FileIcons.getProjectDeleteBitmap())

        self.tree.SetImageList(il)
        self.il = il
        
        # Read configuration
        self.config = ConfigDialog.ConfigData()

        # Threads that watch directories corresponding to open folders
        self.watchers = {}
        
        # Temporary directory for all working files
        self.tempdir = None
        
        # Information for copy/cut/paste of files
        self.clipboard = {'files' : [], 'delete' : False}
        
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
        self.tree.SetItemImage(self.root, self.icons['folder'], 
                               wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root, self.icons['folder-open'],
                                wx.TreeItemIcon_Expanded)

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

        # Notebook syncronization
        try:
            import ed_event
            import extern.flatnotebook as fnb
            #self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGING,
            mw = self.GetGrandParent()
            nb = mw.GetNotebook()
            nb.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
            nb.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnPageClosing)
            mw.Bind(ed_event.EVT_MAINWINDOW_EXIT, self.OnMainWindowExit)
        except ImportError:
            pass

        self.loadProjects()

        #self.tree.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        #self.tree.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        #self.tree.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)

    def saveProjects(self):
        """ Save projects to config file """
        projects = self.config.getProjects()
        self.config.clearProjects()
        for item in self.getProjectPaths():
            if item not in projects:
                self.config.addProject(item)
        self.config.save()
    
    def loadProjects(self):
        """ Add all projects from config to tree """
        items = sorted([(os.path.basename(x), x) 
                        for x in self.config.getProjects().keys()])
        for item in items:
            self.addProject(item[1], save=False) 

    def addProject(self, path, save=True):
        """
        Add a project for the given path
        
        Required Arguments:
        path -- full path to the project directory
        
        Returns: tree node for the project
        
        """
        node = self.tree.AppendItem(self.tree.GetRootItem(),
                                    os.path.basename(path))
        proj = self.tree.AppendItem(node, '')
        self.tree.AppendItem(proj, '')  # <- workaround for windows
        self.tree.SetItemHasChildren(node)
        self.tree.SetPyData(node, {'path' : path})
        self.tree.SetItemImage(node, self.icons['folder'], 
                               wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(node, self.icons['folder-open'],
                                wx.TreeItemIcon_Expanded)

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
        Return a generator to loop over all children of given node
                
        Required Arguments:
        parent -- node to search
        
        Returns: list of child nodes
        
        """
        if not parent.IsOk():
            return
        child, cookie = self.tree.GetFirstChild(parent)
        if not child or not child.IsOk():
            return
        yield child    
        while True:
            if not parent.IsOk():
                return
            child, cookie = self.tree.GetNextChild(parent, cookie)
            if not child or not child.IsOk():
                return
            yield child

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
                    if node.IsOk() and \
                       os.path.isdir(self.tree.GetPyData(node)['path']):
                        self.tree.Collapse(node)
                    if node.IsOk():
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
            except ValueError:
                pass

        if items:
            self.scStatus(items)
        
        self.tree.SortChildren(parent)
        
        evt.Skip()

    def getSelectedNodes(self):
        """ Get the selected items from the tree """
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

        if not self.config.getSyncWithNotebook():
            return

        # Don't sync when a tab was just closed
        if self.isClosing:
            self.isClosing = False
            return
        
        notebook = evt.GetEventObject()
        pg_num = evt.GetSelection()
        txt_ctrl = notebook.GetPage(pg_num)

        # With the text control (ed_stc.EditraStc) this will return the full 
        # path of the file or a wx.EmptyString if the buffer does not contain 
        # an on disk file
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
                except:
                    pass

                self.tree.UnselectAll()
                self.tree.SelectItem(folder)
                break

    def OnRightDown(self, event):
        """Select tree item on mouse button right down event"""
        pt = event.GetPosition()
        item, flags = self.tree.HitTest(pt)
        if item:
            self.log.WriteText("OnRightClick: %s, %s, %s\n" %
                               (self.tree.GetItemText(item), 
                                type(item), item.__class__))
            self.tree.SelectItem(item)

    def OnRightUp(self, event):
        """Enable label editing with right clicks"""
        pt = event.GetPosition()
        item, flags = self.tree.HitTest(pt)
        if item:        
            self.log.WriteText("OnRightUp: %s (manually starting label edit)\n"
                               % self.tree.GetItemText(item))
            self.tree.EditLabel(item)

    def OnBeginEdit(self, event):
        """Begin editing of tree item"""
        self.log.WriteText("OnBeginEdit\n")
 
    def OnEndEdit(self, event):
        """ Finish editing tree node label """
        if event.IsEditCancelled():
            return
        node = event.GetItem()
        data = self.tree.GetPyData(node)
        path = data['path']
        newpath = os.path.join(os.path.dirname(path), event.GetLabel())
        try: 
            os.rename(path, newpath)
            data['path'] = newpath
        except OSError:
            pass

    def OnLeftDClick(self, event):
        """Handle mouse events and update tree"""
        pt = event.GetPosition()
        item, flags = self.tree.HitTest(pt)
        if item:
            self.log.WriteText("OnLeftDClick: %s\n" % self.tree.GetItemText(item))
            parent = self.tree.GetItemParent(item)
            if parent.IsOk():
                self.tree.SortChildren(parent)
        event.Skip()

    def OnSize(self, event):
        """Reset Tree dimensions"""
        w, h = self.GetClientSizeTuple()
        self.tree.SetDimensions(0, 0, w, h)

    def OnItemExpanded(self, event):
        """
        When an item is expanded, track the contents of that directory
        
        """
        parent = event.GetItem()
        if not parent:
            return

        vars = self.tree.GetPyData(parent)
        if not vars:
            return

        path = vars['path']
        if not os.path.isdir(path):
            return
        for item in os.listdir(path):
            self.addPath(parent, item)

        # Delete dummy node from self.addFolder
        self.tree.Delete(self.tree.GetFirstChild(parent)[0])
        self.tree.SortChildren(parent)
        self.addDirectoryWatcher(parent)
        self.scStatus([parent])
        
    def getSCSystem(self, path):
        """ Determine source control system being used on path if any """
        for key, value in self.config.getSCSystems().items():
            if value['instance'].isControlled(path):
                return value            

    def scAdd(self, nodes):
        """ Send an add to repository command to current control system """
        self.scCommand(nodes, 'add')

    def scRemove(self, nodes):
        """ 
        Send an remove from repository command to current control system

        """
        self.scCommand(nodes, 'remove')

    def scUpdate(self, nodes):
        """ Send an update command to current control system """
        self.scCommand(nodes, 'update')

    def scRevert(self, nodes):
        """ Send an revert command to current control system """
        self.scCommand(nodes, 'revert')

    def scCheckout(self, nodes):
        """ Send an checkout command to current control system """
        self.scCommand(nodes, 'checkout') 

    def scStatus(self, nodes):
        """ Send an status command to current control system """
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
        if not self.isSingleRepository(nodes):
            return
            
        while True:
            paths = list()
            for node in nodes:
                try: 
                    data = self.tree.GetPyData(node)
                except:
                    data = {}

                if data.get('sclock', None):
                    continue

                if 'path' not in data:
                    continue
                else:
                    paths.append(data['path'])

            ted = CommitDialog(self, _("Commit Dialog"), 
                               _("Enter your commit message:"), paths)

            if ted.ShowModal() != wx.ID_OK:
                ted.Destroy()
                return

            message = ted.GetValue().strip()
            ted.Destroy()
            if message:
                break

        self.scCommand(nodes, 'commit', message=message)

    def isSingleRepository(self, nodes):
        """ 
        Are all selected files from the same repository ?
        
        Required Arguments:
        nodes -- list of nodes to test
        
        Returns: boolean indicating if all nodes are in the same repository
            (True), or if they are not (False).
        
        """
        previous = ''
        for node in nodes:             
            # Get node data
            try: 
                path = self.tree.GetPyData(node)['path']
            except: 
                continue
            try:
                reppath = self.getSCSystem(path)['instance'].getRepository(path)
            except:
                continue

            if not previous:
                previous = reppath
            elif previous != reppath:
                wx.MessageDialog(self, 
                   _('You can not execute source control commands across multiple repositories.'),
                   _('Selected files are from multiple repositories'), 
                   style=wx.OK|wx.ICON_ERROR).ShowModal()
                return False
        return True

    def scCommand(self, nodes, command, callback=None, **options):
        """
        Run a source control command 
        
        Required Arguments:
        nodes -- selected tree nodes
        command -- name of command type to run
        
        """
        if not self.isSingleRepository(nodes):
            return
            
        try:
            self.GetParent().StartBusy()
        except:
            pass
        
        def run(callback, nodes, command, **options):
            concurrentcmds = ['status', 'history']
            NODE, DATA, SC = 0, 1, 2
            nodeinfo = []
            for node in nodes: 
                if not node.IsOk():
                    return 
                                   
                # Get node data
                try:
                    data = self.tree.GetPyData(node)
                except:
                    data = {}
                
                # node, data, sc
                info = [node, data, None]
                
                # See if the node already has an operation running
                i = 0
                while data.get('sclock', None):
                    time.sleep(1)
                    i += 1
                    if i > self.scTimeout:
                        return

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
                method = getattr(sc['instance'], command, None)
                if method:
                    # Run command (only if it isn't the status command)
                    if command != 'status':
                        rc = self._timeoutCommand(callback, method, 
                             [x[DATA]['path'] for x in nodeinfo], **options)

            finally:
                # Only update status if last command didn't time out
                if command not in ['history', 'revert', 'update'] and rc:
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
            rc = self._timeoutCommand(None, sc['instance'].status,
                                      [data['path']], status=status)
            if not rc:
                return updates
            # Update the icons for the file nodes
            if os.path.isdir(data['path']) and node.IsOk():
                for child in self.getChildren(node):
                    text = self.tree.GetItemText(child)
                    if text not in status:
                        continue
                    if os.path.isdir(os.path.join(data['path'], text)):
                        # Closed folder icon
                        icon = self.icons.get('folder-' + \
                                              status[text].get('status', ''))
                        if icon and child.IsOk():
                            updates.append((self.tree.SetItemImage, child, 
                                            icon, wx.TreeItemIcon_Normal))
                        # Open folder icon
                        icon = self.icons.get('folder-open-' + \
                                              status[text].get('status', ''))
                        if icon and child.IsOk():   
                            updates.append((self.tree.SetItemImage, child, 
                                            icon, wx.TreeItemIcon_Expanded))
                        # Update children status if opened
                        if child.IsOk() and self.tree.IsExpanded(child):
                            self._updateStatus(child, 
                                               self.tree.GetPyData(child), sc)
                    else:
                        icon = self.icons.get('file-' + \
                                              status[text].get('status', ''))
                        if icon and child.IsOk():
                            updates.append((self.tree.SetItemImage, child, 
                                            icon, wx.TreeItemIcon_Normal))
                        #if 'tag' in status[text]:
                        #    updates.append((self.tree.SetToolTip, wx.ToolTip('Tag: %s' % status[text]['tag'])))
            elif node.IsOk():
                text = self.tree.GetItemText(node)
                if text in status:
                    icon = self.icons.get('file-' + status[text].get('status', ''))
                    if icon and node.IsOk():
                        updates.append((self.tree.SetItemImage, node, 
                                        icon, wx.TreeItemIcon_Normal))
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
            try:
                if update[0].IsOk(): 
                    method(*update)
            except: 
                pass
        evt.Skip()
            
    def endSCCommand(self, delayedresult):
        """ Stops progress indicator when source control command is finished """
        try:
            self.GetParent().StopBusy()
        except wx.PyDeadObjectError:
            pass

    def endPaste(self, delayedresult):
        """ Stops progress indicator when paste is finished """
        try:
            self.GetParent().StopBusy()
        except wx.PyDeadObjectError:
            pass
        
    def compareRevisions(self, path, rev1=None, date1=None, 
                         rev2=None, date2=None, callback=None):
        """
        Compare the playpen path to a specific revision, or compare two 
        revisions
        
        Required Arguments:
        path -- absolute path of file to compare
        
        Keyword Arguments:
        rev1/date1 -- first file revision/date to compare against
        rev2/date2 -- second file revision/date to campare against
        
        """
        def diff(path, rev1, date1, rev2, date2, callback):
            """ Do the actual diff of two files by sending the files
            to be compared to the appropriate diff program.

            """
            # Only do files
            if os.path.isdir(path):
                for fname in os.listdir(path):
                    self.compareRevisions(fname, rev1=rev1, date1=date1,
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
                content1 = sc['instance'].fetch([path], rev=rev1, date=date1)
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
                content2 = sc['instance'].fetch([path], rev=rev2, date=date2)
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
                content1 = sc['instance'].fetch([path])
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
            if self.config.getBuiltinDiff() or not (self.config.getDiffProgram()):
                diffwin.GenerateDiff(path2, path1, html=True)
            else:
                subprocess.call([self.config.getDiffProgram(), path2, path1]) 
            
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
        
        Directory watchers keep tree nodes and the file system 
        constantly in sync
        
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
                                               kwargs={'flag':flag,
                                                       'data':node})
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

        for pattern in self.config.getFilters():
            if fnmatch.fnmatchcase(name, pattern):
                return

        data = self.tree.GetPyData(parent)
        if data is None:
            return

        parentpath = data['path']
        itempath = os.path.join(parentpath, name)
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
        self.tree.SetPyData(node, {'path' : os.path.join(parentpath, name)})
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
        self.tree.SetPyData(node, {'path':os.path.join(parentpath, name)})
        self.tree.SetItemImage(node, self.icons['file'], wx.TreeItemIcon_Normal)
        return node

    def OnItemCollapsed(self, event):
        """
        When an item is collapsed, quit tracking the folder contents
        
        """
        item = event.GetItem()
        if not item:
            return
        
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
        """Update what item is currently selected"""
        self.item = event.GetItem()
        if self.item:
            self.log.WriteText("OnSelChanged: %s\n" % \
                                self.tree.GetItemText(self.item))
            if wx.Platform == '__WXMSW__':
                self.log.WriteText("BoundingRect: %s\n" %
                                   self.tree.GetBoundingRect(self.item, True))
            #items = self.tree.GetSelections()
            #print map(self.tree.GetItemText, items)
        event.Skip()

    def OnContextMenu(self, event):
        """ Handle showing context menu to show the commands """
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
            pastable = not (not (self.clipboard['files'])) 
        
        # Is directory controlled by source control
        scenabled = False
        for item in paths:
            if self.getSCSystem(item):
                scenabled = True
                break

        # Add or remove
        if scenabled:
            addremove = (self.popupIDSCRemove, 
                         _("Remove from repository"), 'sc-remove', True)
        else:
            addremove = (self.popupIDSCAdd, _("Add to repository"), 
                         'sc-add', True)
            
        # New file / folder submenu
        newmenu = wx.Menu()
        newmenu.AppendItem(wx.MenuItem(newmenu, self.popupIDNewFolder, _('Folder')))
        newmenu.AppendSeparator()
        for ftype in FILE_TYPES:
            menu_id = wx.NewId()
            newmenu.AppendItem(wx.MenuItem(newmenu, menu_id, ftype))
            self.Bind(wx.EVT_MENU, self.onPopupNewFile, id=menu_id)

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
            (self.popupIDDelete, _("Move to " + TRASH), 'delete', False),
        ]
        for menu_id, title, icon, enabled in items:
            if menu_id is None:
                menu.AppendSeparator()
                continue
            elif icon is not None and not isinstance(icon, basestring):
                item = menu.AppendMenu(menu_id, title, icon)
                item.SetBitmap(self.menuicons['blank'])
                continue

            item = wx.MenuItem(menu, menu_id, _(title))
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
            #print newpath
        #print newpath
        os.makedirs(newpath)

    def onPopupNewFile(self, event):
        """ Create a new file """
        node = self.getSelectedNodes()[0]
        path = self.tree.GetPyData(node)['path']
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        #print path
        # Determine file type
        e_id = event.GetId()
        menu = event.GetEventObject()
        key = None
        for item in menu.GetMenuItems():
            if item.GetId() == e_id:
                key = item.GetLabel()
                break

        if not key or key not in FILE_TYPES:
            return
            
        # Get informatio about file type
        info = FILE_TYPES[key]
        
        # Create unique name
        newpath = os.path.join(path, 'untitled file' + info['ext'])
        i = 1
        while os.path.exists(newpath):
            newpath = os.path.splitext(newpath)[0]
            newpath = re.sub(r'-\d+$', r'', newpath)
            newpath += '-%d%s' % (i, info['ext'])
            i += 1
        
        # Write template info
        f = open(newpath, 'w')
        f.write(info.get('template', '').replace('\n', eol))
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
                        os.system('%s "%s"' % (command, os.path.join(root, f))) 
            else:
                #print command, item
                os.system('%s "%s"' % (command, item)) 

    def onPopupOpen(self, event):
        """ Open the current file using Finder """
        for fname in self.getSelectedPaths():
            subprocess.call([FILEMAN_CMD, fname])

    def onPopupReveal(self, event):
        """ Open the Finder to the parent directory """
        for fname in self.getSelectedPaths():
            subprocess.call([FILEMAN_CMD, os.path.dirname(fname)])

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
            self.tree.SetItemTextColour(item, wx.Colour(192, 192, 192))

    def onPopupCopy(self, event):
        """ Copy the files to the clipboard """
        self.clipboard['files'] = self.getSelectedPaths()
        self.clipboard['delete'] = False
        
    def onPopupPaste(self, event):
        """ Paste the files to the selected directory """
        try: 
            self.GetParent().StartBusy()
        except:
            pass

        dest = self.getSelectedPaths()[0]
        if not os.path.isdir(dest):
            dest = os.path.dirname(dest)
            
        def run(dest):
            delete = self.clipboard['delete']
            self.clipboard['delete'] = False
            newclipboard = []
            for i, fname in enumerate(self.clipboard['files']):
                try:
                    newpath = os.path.join(dest, os.path.basename(fname))
                    newclipboard.append(newpath)
                    if delete:
                        shutil.move(fname, newpath)
                    else:
                        if os.path.isdir(fname):
                            shutil.copytree(fname, newpath, True)
                        else:
                            shutil.copy2(fname, newpath)
                except (OSError, IOError), msg:
                    newclipboard.pop()
                    newclipboard.append(fname)
                    # Do we have more files to copy/move?
                    if i < (len(self.clipboard['files'])-1):
                        rc = wx.MessageDialog(self, 
                          _('The system returned the following message when ' \
                            'attempting to move/copy %s: %s. ' \
                            'Do you wish to continue?' % (fname, msg)), 
                          _('Error occurred when copying/moving files'), 
                          style=wx.YES_NO|wx.YES_DEFAULT|wx.ICON_ERROR).ShowModal()
                        if rc == wx.ID_NO:
                            break 
                    else:
                        rc = wx.MessageDialog(self, 
                          _('The system returned the following message when ' \
                            'attempting to move/copy %s: %s.' % (fname, msg)), 
                          _('Error occurred when copying/moving files'), 
                          style=wx.OK|wx.ICON_ERROR).ShowModal()
            self.clipboard['files'] = newclipboard

        wx.lib.delayedresult.startWorker(self.endPaste, run, wargs=(dest,))

    def onPopupSCRefresh(self, event):
        """ Handle context menu status update command """
        self.scStatus(self.getSelectedNodes())

    def onPopupSCUpdate(self, event):
        """ Handle context menu update repository command """
        self.scUpdate(self.getSelectedNodes())

    def onPopupSCHistory(self, event):
        """ Handle context menu command to show History Window """
        self.scHistory(self.getSelectedNodes())

    def onPopupSCCommit(self, event):
        """ Handle context menu command commit selected nodes """
        self.scCommit(self.getSelectedNodes())

    def onPopupSCRemove(self, event):
        """ Handle context menu command to remove selected nodes """
        self.scRemove(self.getSelectedNodes())

    def onPopupSCRevert(self, event):
        """ Handle context menu command to revert selected nodes """
        self.scRevert(self.getSelectedNodes())

    def onPopupSCAdd(self, event):
        """ Handle context menu command add selected node to source control """
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
                      _('An error occurred when attempting to remove ') + \
                      msg[1] + _('. Do you wish to continue?'),
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
            except (IOError, OSError):
                pass

        nb = self.GetParent().GetOwnerWindow().GetNotebook()

        for item in files:
            if nb.HasFileOpen(item):
                for page in xrange(nb.GetPageCount()):
                    ctrl = nb.GetPage(page)
                    if item == ctrl.GetFileName():
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
                    try:
                        fileinfo[item] = os.stat(os.path.join(path, item))[stat.ST_MTIME]
                    except OSError:
                        pass
            except OSError:
                pass        
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

#-----------------------------------------------------------------------------#

class ProjectPane(wx.Panel):
    """Creates a project pane"""
    ID_REMOVE_PROJECT = wx.NewId()
    ID_ADD_PROJECT = wx.NewId()
    ID_CONFIG = wx.NewId()
    ID_CFGDLG = wx.NewId()
    ID_PROJECTS = wx.NewId()
    PANE_NAME = u'Projects'

    def __init__(self, parent, id=ID_PROJECTPANE, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.NO_BORDER):
        wx.Panel.__init__(self, parent, id, pos, size, style)
        
        # Attributes
        self._mw = parent       # Save ref to owner window
        try:
            import ed_glob
            mb = self._mw.GetMenuBar()
            vm = mb.GetMenuByName("view")
            self._mi = vm.InsertAlpha(self.ID_PROJECTS, _("Projects"), 
                                      _("Open Projects Sidepanel"),
                                      wx.ITEM_CHECK,
                                      after=ed_glob.ID_PRE_MARK)
            vm.Bind(wx.EVT_MENU_OPEN, self.UpdateMenuItem)
        except ImportError:
            ed_glob = None

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.timer = wx.Timer(self)
        self.isBusy = 0

        self.projects = ProjectTree(self, None)

        # Layout Panes
        self.buttonbox = wx.BoxSizer(wx.HORIZONTAL)
        addbutton = wx.BitmapButton(self, self.ID_ADD_PROJECT, 
                                    self.projects.il.GetBitmap(self.projects.icons['project-add']), 
                                    style=wx.NO_BORDER)
        addbutton.SetToolTip(wx.ToolTip(_("Add Project")))
        removebutton = wx.BitmapButton(self, self.ID_REMOVE_PROJECT, 
                                       self.projects.il.GetBitmap(self.projects.icons['project-delete']), 
                                       style=wx.NO_BORDER)
        removebutton.SetToolTip(wx.ToolTip(_("Remove Project")))

        if ed_glob:
            cfgbmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_PREF), wx.ART_MENU)
        else:
            cfgbmp = wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE, wx.ART_MENU)
        configbutton = wx.BitmapButton(self, self.ID_CONFIG, 
                                       cfgbmp, style=wx.NO_BORDER)
        configbutton.SetToolTip(wx.ToolTip(_("Configure")))

        self.busy = wx.Gauge(self, size=(50, 16), style=wx.GA_HORIZONTAL)
        self.busy.Hide()

        if wx.Platform == '__WXGTK__':
            spacer = (3, 3)
            self.buttonbox.Add((5, 24))
        else:
            spacer = (10, 10)
            self.buttonbox.Add((10, 24))

        self.buttonbox.Add(addbutton, 0, wx.ALIGN_CENTER_VERTICAL)
        self.buttonbox.Add(spacer)
        self.buttonbox.Add(removebutton, 0, wx.ALIGN_CENTER_VERTICAL)
        self.buttonbox.Add(spacer)
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
        self.Bind(ConfigDialog.EVT_CONFIG_EXIT, self.OnCfgClose)

    def __del__(self):
        """Make sure the timer is stopped"""
        if self.timer.IsRunning():
            self.timer.Stop()

    def GetOwnerWindow(self):
        """Return reference to mainwindow that created this panel"""
        return self._mw

    def OnCfgClose(self, evt):
        """Recieve configuration data when dialog is closed"""
        e_id = evt.GetId()
        if e_id == self.ID_CFGDLG:
            self.projects.config.save()
        else:
            evt.Skip()

    def OnPaint(self, evt):
        """Paint the button area of the panel with a gradient"""
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)

        # Get some system colors
        col1 = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)
        col2 = AdjustColour(col1, 50)
        col1 = AdjustColour(col1, -50)

        rect = self.GetRect()
        grad = gc.CreateLinearGradientBrush(0, 1, 0, 
                                            self.buttonbox.GetSize()[1],
                                            col2, col1)
        gc.SetBrush(grad)

        # Create the background path
        path = gc.CreatePath()
        path.AddRectangle(0, 0, rect.width - 0.5, rect.height - 0.5)

        gc.SetPen(wx.Pen(AdjustColour(col1, -60), 1))
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
            if not self.FindWindowById(self.ID_CFGDLG):
                cfg = ConfigDialog.ConfigDialog(self, self.ID_CFGDLG, 
                                                self.projects.config) 
                cfg.Show()
            else:
                pass
        else:
            evt.Skip()

    def OnShowProjects(self, evt):
        """ Shows the projects """
        if evt.GetId() == self.ID_PROJECTS and profiler:
            mgr = self._mw.GetFrameManager()
            pane = mgr.GetPane(self.PANE_NAME)
            if pane.IsShown():
                pane.Hide()
                profiler.Profile_Set('Projects.Show', False)
            else:
                pane.Show()
                profiler.Profile_Set('Projects.Show', True)
            mgr.Update()
        else:
            evt.Skip()

    def UpdateMenuItem(self, evt):
        """Update the check mark for the menu item"""
        mgr = self._mw.GetFrameManager()
        pane = mgr.GetPane(self.PANE_NAME)
        self._mi.Check(pane.IsShown())
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
            self.buttonbox.Add(self.busy, 0, 
                               wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
            self.buttonbox.Add((10, 10), 0, wx.ALIGN_RIGHT)

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

        self._entry = wx.TextCtrl(self, size=(400, 250), style=wx.TE_MULTILINE)
        font = self._entry.GetFont()
        if wx.Platform == '__WXMAC__':
            font.SetPointSize(12)
            self._entry.MacCheckSpelling(True)
        else:
            font.SetPointSize(10)
        self._entry.SetFont(font)

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
        msg.append(u': ' + (u'-' * 40))
        msg.append(u": Lines beginning with `:' are removed automatically")
        msg.append(u": Modified Files:")
        for path in files:
            tmp = ":\t%s" % path
            msg.append(tmp)
        msg.append(u': ' + (u'-' * 40))
        msg.extend([u'', u''])
        msg = os.linesep.join(msg)
        self._entry.SetValue(msg)
        self._entry.SetInsertionPoint(self._entry.GetLastPosition())

    def _DoLayout(self):
        """ Used internally to layout dialog before being shown """
        sizer = wx.BoxSizer(wx.VERTICAL)
        csizer = wx.BoxSizer(wx.HORIZONTAL)
        bsizer = wx.BoxSizer(wx.HORIZONTAL)
        esizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer.Add((10, 10), 0)
        csizer.Add((10, 10), 0)
        csizer.Add(self._caption, 0, wx.ALIGN_LEFT, 5)
        sizer.Add(csizer, 0)
        sizer.Add((10, 10), 0)
        esizer.AddMany([((10, 10), 0), 
                        (self._entry, 1, wx.EXPAND), 
                        ((10, 10), 0)])
        sizer.Add(esizer, 0, wx.EXPAND)
        bsizer.AddStretchSpacer()
        bsizer.AddMany([(self._cancel, 0, wx.ALIGN_RIGHT, 5), ((5, 5)),
                       (self._commit, 0, wx.ALIGN_RIGHT, 5), ((5, 5))])
        sizer.Add((10, 10))
        sizer.Add(bsizer, 0, wx.ALIGN_RIGHT)
        sizer.Add((10, 10))
        self.SetSizer(sizer)
        self.SetInitialSize()

    def GetValue(self):
        """Return the value of the commit message"""
        txt = self._entry.GetString(0, self._entry.GetLastPosition()).strip()
        txt = txt.replace('\r\n', '\n')
        return os.linesep.join([ x for x in txt.split('\n') 
                                 if not x.lstrip().startswith(':') ])

#-----------------------------------------------------------------------------#

class ExecuteCommandDialog(wx.Dialog):
    """ Creates a dialog for getting a shell command to execute """
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
        """ Test Application """
        def OnInit(self):
            """ Frame for showing and testing projects outside of Editra """
            frame = wx.Frame(None, -1, "Hello from wxPython")
            ProjectPane(frame)
            frame.Show(True)
            self.SetTopWindow(frame)
            return True

    APP = MyApp(0)
    APP.MainLoop()

