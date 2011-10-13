###############################################################################
# Name: ProjectMgr.py                                                         #
# Purpose: Project File Manager                                               #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2011 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
Project File Manager

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
import ebmlib
import eclib
import ed_basewin
import syntax.synglob as synglob

# Local libs
import PyStudio.Common.Images as Images
import PyStudio.Project.ProjectXml as ProjectXml
import PyStudio.Project.ProjectFile as ProjectFile
import PyStudio.Project.NewProjectDlg as NewProjectDlg

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class ProjectManager(ed_basewin.EdBaseCtrlBox):
    """Main UI component for the Project feature."""
    PANE_NAME = u"PyProject"
    ID_NEW_PROJECT = wx.NewId()
    ID_OPEN_PROJECT = wx.NewId()
    ID_CONF_PROJECT = wx.NewId()
    def __init__(self, parent):
        """Create the manager window
        @param parent: MainWindow instance

        """
        super(ProjectManager, self).__init__(parent)

        # Attributes
        self._mw = parent
        self._tree = ProjectTree(self)

        # Setup
        cbar = self.CreateControlBar(wx.TOP)
        # Setup the project button
        self.projbtn = cbar.AddPlateButton(bmp=Images.Project.Bitmap)
        pmenu = wx.Menu()
        pmenu.Append(ProjectManager.ID_NEW_PROJECT, _("New Project"))
        pmenu.Append(ProjectManager.ID_OPEN_PROJECT, _("Open Project"))
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

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnNewFile, nfilebtn)
        self.Bind(wx.EVT_BUTTON, self.OnNewPackage, npkgbtn)
        self.Bind(wx.EVT_BUTTON, self.OnNewFolder, nfolderbtn)
        self.Bind(wx.EVT_MENU, self.OnMenu)

    #---- Properties ----#

    MainWindow = property(lambda self: self._mw)
    Tree = property(lambda self: self._tree)

    #---- Implementation ----#

    def OnNewFolder(self, evt):
        pass

    def OnNewPackage(self, evt):
        pass

    def OnNewFile(self, evt):
        pass

    def OnMenu(self, evt):
        """Handles menu events for the Project Manager"""
        actions = { ProjectManager.ID_NEW_PROJECT  : self.NewProject,
                    ProjectManager.ID_OPEN_PROJECT : self.OpenProject,
                    ProjectManager.ID_CONF_PROJECT : self.ShowConfig }
        actions.get(evt.Id, evt.Skip)()

    def NewProject(self):
        """Create a new project"""
        dlg = NewProjectDlg.NewProjectDlg(self.MainWindow)
        dlg.CenterOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            proj = dlg.GetProjectData()
            if proj.CreateProject():
                # Create the project file
                pxml = ProjectXml.ProjectXml(name=proj.ProjectName)
                def GenProject(obj, basepath):
                    """Recursively populate the project file based on the
                    project that was created.

                    """
                    for item in os.listdir(basepath):
                        fpath = os.path.join(basepath, item)
                        if os.path.isdir(fpath):
                            nobj = ProjectXml.Folder(name=item)
                            obj.folders.append(nobj)
                            GenProject(nobj, fpath) # recurse
                GenProject(pxml, proj.ProjectPath)
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
                            wildcard=u"PyStudio Project (*.psp)|*.psp", # TODO: decide file extension
                            style=wx.FD_OPEN)
        dlg.CenterOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            pass
        dlg.Destroy()

    def ShowConfig(self):
        """Show the configuration for the current project"""
        pass

#-----------------------------------------------------------------------------#

class ProjectTree(eclib.FileTree):
    """Provides a tree view of all the files and packages in a project."""
    # ImageList indexes
    IMAGES = range(4)
    IMG_FOLDER,\
    IMG_PACKAGE,\
    IMG_FILE,\
    IMG_PYTHON = IMAGES
    IMGMAP = { IMG_FOLDER  : ed_glob.ID_FOLDER,
               IMG_PACKAGE : ed_glob.ID_PACKAGE,
               IMG_FILE    : ed_glob.ID_FILE,
               IMG_PYTHON  : synglob.ID_LANG_PYTHON }

    def __init__(self, parent):
        super(ProjectTree, self).__init__(parent)

        # Attributes
        self._proj = None

        # Setup
        self.SetupImageList()

    #---- Properties ----#

    Project = property(lambda self: self._proj,
                       lambda self, proj: self.LoadProject(proj))

    #---- Overrides ----#

    def DoGetFileImage(self, path):
        """Get the image for the given item"""
        if os.path.isdir(path):
            return ProjectTree.IMG_FOLDER
        lpath = path.lower()
        if lpath.endswith(u".py") or lpath.endswith(u".pyw"):
            return ProjectTree.IMG_PYTHON
        else:
            return ProjectTree.IMG_FILE

    def DoSetupImageList(self):
        """Setup the image list for this control"""
        for img in ProjectTree.IMAGES:
            imgid = ProjectTree.IMGMAP[img]
            bmp = wx.ArtProvider_GetBitmap(str(imgid), wx.ART_MENU)
            self.ImageList.Add(bmp)

    #---- Implementation ----#

    def LoadProject(self, proj):
        """Load the given project
        @param proj: ProjectFile instance

        """
        self.DeleteChildren(self.RootItem)
        self._proj = proj

        # Repopulate root of tree
        self.AddWatchDirectory(self._proj.ProjectRoot)

