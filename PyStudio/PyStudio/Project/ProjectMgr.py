###############################################################################
# Name: ProjectMgr.py                                                         #
# Purpose: Project File Manager                                               #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2011 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
Project File Manager

Main PyProject UI components for integration into Editra user interface.

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Dependencies
import os
import wx

# Editra libs
import ed_glob
import util
import ebmlib
import eclib
import ed_basewin
import ed_menu
import ed_msg
import syntax.synglob as synglob

# Local libs
from PyStudio.Common import ToolConfig
import PyStudio.Common.Images as Images
from PyStudio.Common.PyStudioUtils import PyStudioUtils
from PyStudio.Common.Messages import PyStudioMessages
import PyStudio.Project.ProjectXml as ProjectXml
import PyStudio.Project.ProjectFile as ProjectFile
import PyStudio.Project.NewProjectDlg as NewProjectDlg
import PyStudio.Project.ProjectUtil as ProjectUtil
from PyStudio.Controller.FileController import FileController

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class ProjectManager(ed_basewin.EdBaseCtrlBox):
    """Main UI component for the Project feature."""
    PANE_NAME = u"PyProject"
    ID_NEW_PROJECT = wx.NewId()
    ID_IMPORT_PROJECT = wx.NewId()
    ID_OPEN_PROJECT = wx.NewId()
    ID_CONF_PROJECT = wx.NewId()
    def __init__(self, parent):
        """Create the manager window
        @param parent: MainWindow instance

        """
        super(ProjectManager, self).__init__(parent)
        util.Log("[PyProject][info] Creating ProjectManager instance")

        # Attributes
        self._mw = parent
        self._tree = ProjectTree(self)

        # Setup
        cbar = self.CreateControlBar(wx.TOP)
        # Setup the project button
        self.projbtn = cbar.AddPlateButton(bmp=Images.Project.Bitmap)
        pmenu = wx.Menu()
        pmenu.Append(ProjectManager.ID_NEW_PROJECT, _("New Project"),
                     _("Create a new project"))
        pmenu.Append(ProjectManager.ID_IMPORT_PROJECT, _("Import Project"),
                     _("Import an existing project"))
        pmenu.Append(ProjectManager.ID_OPEN_PROJECT, _("Open Project"),
                     _("Open an existing PyProject project file"))
        pmenu.AppendSeparator()
        item = wx.MenuItem(pmenu, 
                           ProjectManager.ID_CONF_PROJECT, 
                           _("Project Settings"))
        item.Bitmap = wx.ArtProvider_GetBitmap(str(ed_glob.ID_PREF), wx.ART_MENU)
        pmenu.AppendItem(item)
        self.projbtn.SetMenu(pmenu)
        # Setup additional buttons
        bmp = wx.ArtProvider_GetBitmap(str(synglob.ID_LANG_PYTHON), wx.ART_MENU)
        cbar.AddControl(wx.StaticLine(cbar, size=(1,16), style=wx.LI_VERTICAL))
        nfilebtn = cbar.AddPlateButton(bmp=bmp)
        nfilebtn.ToolTip = wx.ToolTip(_("New Module"))
        bmp = wx.ArtProvider_GetBitmap(str(ed_glob.ID_PACKAGE), wx.ART_MENU)
        npkgbtn = cbar.AddPlateButton(bmp=bmp)
        npkgbtn.ToolTip = wx.ToolTip(_("New Package"))
        bmp = wx.ArtProvider_GetBitmap(str(ed_glob.ID_NEW_FOLDER), wx.ART_MENU)
        nfolderbtn = cbar.AddPlateButton(bmp=bmp)
        nfolderbtn.ToolTip = wx.ToolTip(_("New Folder"))
        self.SetWindow(self._tree)

        # Post Initialization
        if ToolConfig.GetConfigValue(ToolConfig.TLC_LOAD_LAST_PROJECT, True):
            lproj = ToolConfig.GetConfigValue(ToolConfig.TLC_LAST_PROJECT, None)
            util.Log("[PyProject][info] Loading last project %s" % repr(lproj))
            if lproj and os.path.exists(lproj):
                self.DoOpenProject(lproj)

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnNewFile, nfilebtn)
        self.Bind(wx.EVT_BUTTON, self.OnNewPackage, npkgbtn)
        self.Bind(wx.EVT_BUTTON, self.OnNewFolder, nfolderbtn)
        self.Bind(wx.EVT_MENU, self.OnMenu)

    #---- Properties ----#

    MainWindow = property(lambda self: self._mw)
    Tree = property(lambda self: self._tree)

    #---- Implementation ----#

    def DoOpenProject(self, path):
        """Open the project file and display it in the L{ProjectTree}
        @param path: PyStudio Project file path

        """
        pxml = ProjectXml.ProjectXml.Load(path)
        pfile = ProjectFile.ProjectFile(pxml, path)
        self.Tree.LoadProject(pfile)

    def OnNewFolder(self, evt):
        pass

    def OnNewPackage(self, evt):
        pass

    def OnNewFile(self, evt):
        pass

    def OnMenu(self, evt):
        """Handles menu events for the Project Manager"""
        actions = { ProjectManager.ID_NEW_PROJECT  : self.NewProject,
                    ProjectManager.ID_IMPORT_PROJECT : self.ImportProject,
                    ProjectManager.ID_OPEN_PROJECT : self.OpenProject,
                    ProjectManager.ID_CONF_PROJECT : self.ShowConfig }
        actions.get(evt.Id, evt.Skip)()

    def ImportProject(self):
        """Prompt the user to import an existing project"""
        cbuf = wx.GetApp().GetCurrentBuffer()
        if cbuf and hasattr(cbuf, 'GetFileName'):
            fname = cbuf.GetFileName()
            dname = os.path.dirname(fname)
        # TODO: Enhancement - support loading/import other project types (i.e pydev)
        dlg = wx.DirDialog(self.MainWindow, _("Import Project Directory"),
                           dname)
        if dlg.ShowModal() == wx.ID_OK:
            proj = dlg.Path
            projName = os.path.basename(proj)
            pxml = ProjectXml.ProjectXml(name=projName)
            # Write out the new project file
            ppath = os.path.join(proj, u"%s.psp" % projName)
            if ebmlib.PathExists(ppath):
                result = wx.MessageBox(_("The project '%s' already exists.\nDo you wish to overwrite it?") % projName,
                                       _("Project Exists"),
                                       style=wx.ICON_WARNING|wx.YES_NO)
                if result == wx.ID_NO:
                    return
            pfile = ProjectFile.ProjectFile(pxml, ppath)
            pfile.Save()
            self.Tree.LoadProject(pfile) # Load the view

    def NewProject(self):
        """Create a new project"""
        dlg = NewProjectDlg.NewProjectDlg(self.MainWindow)
        dlg.CenterOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            proj = dlg.GetProjectData()
            if proj.CreateProject():
                # Create the project file
                pxml = ProjectXml.ProjectXml(name=proj.ProjectName)
                pxml.folders = proj.Template.folders
                pxml.packages = proj.Template.packages
                def CleanFiles(fold):
                    """Remove template files from project configuration"""
                    for d in fold:
                        d.files = list()
                        CleanFiles(d.folders)
                        CleanFiles(d.packages)
                CleanFiles(pxml.folders)
                CleanFiles(pxml.packages)
                # Write the project file out to the new project directory
                ppath = os.path.join(proj.ProjectPath, u"%s.psp" % proj.ProjectName)
                pfile = ProjectFile.ProjectFile(pxml, ppath)
                pfile.Save()
                self.Tree.LoadProject(pfile) # Load the view
            else:
                pass # TODO: error handling
        dlg.Destroy()

    def OpenProject(self):
        """Show the project open dialog"""
        dname = u""
        cbuf = wx.GetApp().GetCurrentBuffer()
        if cbuf and hasattr(cbuf, 'GetFileName'):
            fname = cbuf.GetFileName()
            dname = os.path.dirname(fname)
        dlg = wx.FileDialog(self.MainWindow, _("Open Project"),
                            defaultDir=dname,
                            wildcard=u"PyStudio Project (*.psp)|*.psp",
                            style=wx.FD_OPEN)
        dlg.CenterOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            self.DoOpenProject(dlg.Path)
        dlg.Destroy()

    def ShowConfig(self):
        """Show the configuration for the current project"""
        pass

#-----------------------------------------------------------------------------#

class ProjectTree(eclib.FileTree):
    """Provides a tree view of all the files and packages in a project."""
    # Context Menu Ids
    ID_OPEN_FILE   = wx.NewId()
    ID_NEW_SUBMENU = wx.NewId()
    ID_NEW_FILE    = wx.NewId()
    ID_NEW_FOLDER  = wx.NewId()
    ID_NEW_PACKAGE = wx.NewId()
    ID_PROPERTIES  = wx.NewId()
    ID_RENAME_FILE = wx.NewId()

    def __init__(self, parent):
        super(ProjectTree, self).__init__(parent)

        # Attributes
        self._proj = None
        self._menu = ebmlib.ContextMenuManager()
        self._monitor = ebmlib.DirectoryMonitor()
        self._monitor.SubscribeCallback(self.OnFilesChanged)
        self._monitor.StartMonitoring()

        # Setup
        self.SetupImageList()

        # Event Handlers
        self.Bind(wx.EVT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy, self)

        # Message Handlers
        ed_msg.Subscribe(self.OnGetProject, PyStudioMessages.PYSTUDIO_PROJECT_GET)

    #---- Properties ----#

    def __GetFileController(self):
        opt = self._proj.GetOption(u"filesystem")
        if opt is None:
            # Default to base controller
            opt = u"OS"
        return FileController.FactoryCreate(opt)
    FileController = property(lambda self: self.__GetFileController())
    Project = property(lambda self: self._proj,
                       lambda self, proj: self.LoadProject(proj))

    #---- Overrides ----#

    def DoBeginEdit(self, item):
        """Handle when an item is requested to be edited"""
        # TODO: pass handling to see if the path can be edited to FileController?
        if self.IsProjectRoot(item):
            return False
        return True

    def DoEndEdit(self, item, newlabel):
        """Handle after a user has made changes to a label"""
        path = self.GetPyData(item)
        # TODO: check access rights and validate input
        newpath = os.path.join(os.path.dirname(path), newlabel)
        return self.FileController.Rename(path, newpath)

    def DoItemActivated(self, item):
        """Override to handle item activation
        @param item: TreeItem

        """
        path = self.GetPyData(item)
        if path and os.path.exists(path):
            if not os.path.isdir(path):
                PyStudioUtils.GetEditorOrOpenFile(self.Parent.MainWindow, path)
        # TODO notify failure to open

    def DoItemCollapsed(self, item):
        """Handle when an item is collapsed"""
        d = self.GetPyData(item)
        self._monitor.RemoveDirectory(d)
        super(ProjectTree, self).DoItemCollapsed(item)

    def DoItemExpanding(self, item):
        """Handle when an item is expanding to display the folder contents
        @param item: TreeItem

        """
        d = None
        try:
            d = self.GetPyData(item)
        except wx.PyAssertionError:
            util.Log("[PyStudio][err] ProjectTree.DoItemExpanding")
            return

        if d and os.path.exists(d):
            contents = ProjectTree.GetDirContents(d)
            # Filter contents
            dirs = list()
            files = list()
            for p in contents:
                if os.path.isdir(p) and not p.startswith('.'): # TODO: config
                    dirs.append(p)
                else:
                    ext = ebmlib.GetFileExtension(p)
                    if ext not in (u'pyc', u'pyo', u'psp'): # TODO use configuration
                        files.append(p)
            dirs.sort()
            files.sort()
            dirs.extend(files)
            for p in dirs:
                self.AppendFileNode(item, p)
            self.SortChildren(item)
            self._monitor.AddDirectory(d)

    def DoGetFileImage(self, path):
        """Get the image for the given item"""
        iconmgr = ProjectUtil.FileIcons
        if os.path.isdir(path):
            for p in ProjectTree.GetDirContents(path):
                if p.endswith(u"__init__.py"):
                    return iconmgr.IMG_PACKAGE
            return iconmgr.IMG_FOLDER
        lpath = path.lower()
        if lpath.endswith(u".py") or lpath.endswith(u".pyw"):
            return iconmgr.IMG_PYTHON
        else:
            return iconmgr.IMG_FILE

    def DoSetupImageList(self):
        """Setup the image list for this control"""
        ProjectUtil.FileIcons.PopulateImageList(self.ImageList)

    def DoShowMenu(self, item):
        """Show a context menu for the selected item
        @param item: TreeItem

        """
        path = self.GetPyData(item)
        self._menu.Clear()
        menu = wx.Menu()
        # Populate menu for current item with standard options
        if not os.path.isdir(path):
            menu.Append(ProjectTree.ID_OPEN_FILE, _("Open..."))
            menu.AppendSeparator()
        newmenu = wx.Menu()
        for data in ((ProjectTree.ID_NEW_FILE, _("New File..."), ed_glob.ID_NEW),
                     (ProjectTree.ID_NEW_FOLDER, _("New Folder..."), ed_glob.ID_NEW_FOLDER),
                     (ProjectTree.ID_NEW_PACKAGE, _("New Package..."), ed_glob.ID_PACKAGE)):
            mitem = wx.MenuItem(newmenu, data[0], data[1])
            mitem.SetBitmap(wx.ArtProvider_GetBitmap(str(data[2]), wx.ART_MENU))
            newmenu.AppendItem(mitem)
        menu.AppendMenu(ProjectTree.ID_NEW_SUBMENU, _("New"), newmenu)
        menu.AppendSeparator()
        if not self.IsProjectRoot(item):
            menu.Append(ed_glob.ID_DELETE, _("Move to trash"))
            menu.Append(ProjectTree.ID_RENAME_FILE, _("Rename"))
            menu.AppendSeparator()

        ccount = menu.GetMenuItemCount()

        # Menu customization interface
        # Allow other components to add custom menu options
        self._menu.SetUserData('path', path) # path of item that was clicked on
        self._menu.SetUserData('itemId', item)
        ed_msg.PostMessage(PyStudioMessages.PYSTUDIO_PROJECT_MENU,
                           self._menu, self.Parent.MainWindow.Id)

        # Add properties
        if ccount < menu.GetMenuItemCount():
            menu.AppendSeparator()
        mitem = menu.Append(ProjectTree.ID_PROPERTIES, _("Properties"))
        mitem.SetBitmap(wx.ArtProvider_GetBitmap(str(ed_glob.ID_PREF), wx.ART_MENU))

        # Show the popup Menu
        self._menu.Menu = menu
        self._menu.SetUserData('path', path)
        self.PopupMenu(self._menu.Menu)

    #---- Event Handlers ----#
  
    def OnContextMenu(self, evt):
        """Handle context menu events"""
        e_id = evt.Id
        path = self._menu.GetUserData('path')
        dname = path
        if not os.path.isdir(path):
            dname = os.path.dirname(path)

        if e_id == ProjectTree.ID_OPEN_FILE:
            PyStudioUtils.GetEditorOrOpenFile(self.Parent.MainWindow, path)
        elif e_id == ProjectTree.ID_NEW_FILE:
            name = wx.GetTextFromUser(_("Enter file name:"), _("New File"),
                                      parent=self.Parent.MainWindow)
            if name:
                self.FileController.CreateFile(dname, name)
        elif e_id in (ProjectTree.ID_NEW_FOLDER, ProjectTree.ID_NEW_PACKAGE):
            if e_id == ProjectTree.ID_NEW_FOLDER:
                msg = _("Enter folder name:")
                caption = _("New Folder")
            else:
                msg = _("Enter package name:")
                caption = _("New Package")
            name = wx.GetTextFromUser(msg, caption,
                                      parent=self.Parent.MainWindow)
            if name:
                self.FileController.CreateFolder(dname, name)
                # TODO need return val from createfolder
                if e_id == ProjectTree.ID_NEW_PACKAGE:
                    path = os.path.join(dname, name)
                    self.FileController.CreateFile(path, "__init__.py")
        elif e_id == ed_glob.ID_DELETE:
            # TODO need error handling?
            if dname == path:
                cmsg = _("Are you sure you want to delete '%s' and all of its contents?")
            else:
                cmsg = _("Are you sure you want to delete '%s'?")
            name = os.path.basename(path)
            result = wx.MessageBox(cmsg % name, _("Delete?"), 
                                   style=wx.YES_NO|wx.CENTER|wx.ICON_QUESTION)
            if result == wx.YES:
                self.FileController.MoveToTrash(path)
        elif e_id == ProjectTree.ID_RENAME_FILE:
            item = self._menu.GetUserData('itemId')
            if item:
                self.EditLabel(item)
        elif e_id == ProjectTree.ID_PROPERTIES:
            pass # TODO: project properties dialog
        else:
            # Handle Custom Menu options
            handler = self._menu.GetHandler(e_id)
            if handler:
                handler(path)

    def OnDestroy(self, evt):
        """Cleanup when window is destroyed"""
        util.Log("[PyProject][info] ProjectTree.OnDestroy")
        if self and evt.Id == self.Id:
            util.Log("PyProject][info] Doing Cleanup in Destroy...")
            self._menu.Clear()
        evt.Skip()

    def OnFilesChanged(self, added, deleted, modified):
        """DirectoryMonitor callback - synchronize the view
        with the filesystem.

        """
        nodes = self.GetExpandedNodes()
        visible = list()
        for node in nodes:
            visible.extend(self.GetChildNodes(node))

        # Remove any deleted file objects
        for fobj in deleted:
            for item in visible:
                path = self.GetPyData(item)
                if fobj.Path == path:
                    self.Delete(item)
                    visible.remove(item)
                    break

        # Add any new file objects to the view
        needsort = list()
        for fobj in added:
            dpath = os.path.dirname(fobj.Path)
            for item in nodes:
                path = self.GetPyData(item)
                if path == dpath:
                    self.AppendFileNode(item, fobj.Path)
                    if item not in needsort:
                        needsort.append(item)
                    break

        # Resort display
        for item in needsort:
            self.SortChildren(item)

        # TODO: pass modification notifications onto FileController interface
        #       to handle.
#        for fobj in modified:
#            pass

    def OnCompareItems(self, item1, item2):
        """Handle SortItems"""
        data = self.GetPyData(item1)
        if data is not None:
            path1 = int(not os.path.isdir(data))
        else:
            path1 = 0
        tup1 = (path1, data.lower())

        data2 = self.GetPyData(item2)
        if data2 is not None:
            path2 = int(not os.path.isdir(data2))
        else:
            path2 = 0
        tup2 = (path2, data2.lower())

        if tup1 < tup2:
            return -1
        elif tup1 == tup2:
            return 0
        else:
            return 1

    def GetMainWindow(self):
        return self.Parent.MainWindow

    @ed_msg.mwcontext
    def OnGetProject(self, msg):
        """Return the project file reference to the client that
        requested it.

        """
        msg.Data['project'] = self.Project

    def IsProjectRoot(self, item):
        """Is the given item the current project root
        @param item: TreeItem
        @return: bool

        """
        path = self.GetPyData(item)
        if self.Project and self.Project.ProjectRoot:
            return path == self.Project.ProjectRoot
        return False

    #---- Implementation ----#

    def LoadProject(self, proj):
        """Load the given project
        @param proj: ProjectFile instance or None to clear

        """
        self.DeleteChildren(self.RootItem)
        if self.Project and self.Project.ProjectRoot:
            self.RemoveWatchDirectory(self._proj.ProjectRoot)
        self._proj = proj
        if not self.Project:
            return # cleared/closed current project

        # Repopulate root of tree
        item = self.AddWatchDirectory(self.Project.ProjectRoot)
        if item:
            self._projItem = item
            iconmgr = ProjectUtil.FileIcons
            self.SetItemImage(item, iconmgr.IMG_PROJECT)
            self.Expand(item)
            # Update last project info
            ToolConfig.SetConfigValue(ToolConfig.TLC_LAST_PROJECT, self.Project.Path)
            ed_msg.PostMessage(PyStudioMessages.PYSTUDIO_PROJECT_LOADED, 
                               self.Project, self.Parent.MainWindow.Id)
        else:
            self._projItem = None
            wx.MessageBox(_("Unable to load project: %s") % self.Project.ProjectName,
                          _("PyStudio Error"), style=wx.OK|wx.CENTER|wx.ICON_ERROR)
            return
