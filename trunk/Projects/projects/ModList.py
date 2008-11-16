###############################################################################
# Name: ModList.py                                                            #
# Purpose: Enumerate modified, added, deleted files in a list                 #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
File Modification List

Display component for displaying file status for a repository and allowing for
checking, reverts, ect...

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#--------------------------------------------------------------------------#
# Imports
import os
import threading
import wx
import wx.lib.mixins.listctrl as listmix

# Local Imports
import FileIcons
import ConfigDialog
import ScCommand
import ProjCmnDlg
from HistWin import HistoryWindow

# Editra Imports
import ed_glob
import ed_msg
import eclib.ctrlbox as ctrlbox
import eclib.platebtn as platebtn
import eclib.elistmix as elistmix

#--------------------------------------------------------------------------#
# Globals

# Menu Id's
ID_UPDATE              = wx.NewId()
ID_COMPARE_TO_PREVIOUS = wx.NewId()
ID_COMMIT              = wx.NewId()
ID_REVERT              = wx.NewId()
ID_REVISION_HIST       = wx.NewId()

# Control Id's
ID_REPO_CHOICE = wx.NewId()

# Status Keys used by SourceControl modules
STATUS = { u'modified' : u'M',
           u'added'    : u'A',
           u'deleted'  : u'D',
           u'conflict' : u'C',
           u'unknown'  : u'?' }
           
_ = wx.GetTranslation

#--------------------------------------------------------------------------#

class RepoModBox(ctrlbox.ControlBox):
    """Repository modification list container window"""
    def __init__(self, parent):
        ctrlbox.ControlBox.__init__(self, parent)

        # Attributes
        self._list = RepoModList(self)
        self._config = ConfigDialog.ConfigData() # Singleton Config Obj
        self._crepo = 0
        self._ctrl = ScCommand.SourceController(self)
        self._repos = self.FindRepos(self._config['projects'].keys())
        self._repo_ch = None

        # Setup
        self.__DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, lambda evt: self.DoCommit(), id=ID_COMMIT)
        self.Bind(wx.EVT_BUTTON, lambda evt: self.DoUpdate(), id=ID_UPDATE)
        self.Bind(wx.EVT_BUTTON,
                  lambda evt: self.DoStatusRefresh(), id=wx.ID_REFRESH)
        self.Bind(wx.EVT_BUTTON,
                  lambda evt: self.DoRevert(), id=wx.ID_REVERT)
        self.Bind(wx.EVT_CHOICE, self.OnChoice, id=ID_REPO_CHOICE)
#        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateUI)

    def __DoLayout(self):
        """Layout and setup the results screen ui"""
        ctrlbar = ctrlbox.ControlBar(self, style=ctrlbox.CTRLBAR_STYLE_GRADIENT)
        if wx.Platform == '__WXGTK__':
            ctrlbar.SetWindowStyle(ctrlbox.CTRLBAR_STYLE_DEFAULT)

        def cmptup(x, y):
            if x[1] < y[1]:
                return -1
            elif x[1] == y[1]:
                return 0
            else:
                return 1

        # Repository
        ctrlbar.AddControl(wx.StaticText(ctrlbar, label=_("Repository") + u":"))
        projects = sorted([(x, os.path.basename(x)) for x in self._repos], cmptup)
        self._repos = [x[0] for x in projects]
        self._repo_ch = wx.Choice(ctrlbar, ID_REPO_CHOICE,
                                  choices=[x[1] for x in projects])
        if len(self._repos):
            self._repo_ch.SetToolTipString(self._repos[0])
        ctrlbar.AddControl(self._repo_ch)

        ctrlbar.AddStretchSpacer()

        # Refresh Button
        refresh = platebtn.PlateButton(ctrlbar, wx.ID_REFRESH, _("Refresh"),
                                       FileIcons.getScStatusBitmap(),
                                       style=platebtn.PB_STYLE_NOBG)
        ctrlbar.AddControl(refresh, wx.ALIGN_RIGHT)

        # Update
        update = platebtn.PlateButton(ctrlbar, ID_UPDATE, _("Update"),
                                      FileIcons.getScUpdateBitmap(),
                                      style=platebtn.PB_STYLE_NOBG)
        ctrlbar.AddControl(update, wx.ALIGN_RIGHT)

        # Commit
        commit = platebtn.PlateButton(ctrlbar, ID_COMMIT, _("Commit"),
                                      FileIcons.getScCommitBitmap(),
                                      style=platebtn.PB_STYLE_NOBG)
        ctrlbar.AddControl(commit, wx.ALIGN_RIGHT)

        # Clear Button
        revert = platebtn.PlateButton(ctrlbar, ID_REVERT, _("Revert"),
                                      FileIcons.getScRevertBitmap(),
                                      style=platebtn.PB_STYLE_NOBG)
        ctrlbar.AddControl(revert, wx.ALIGN_RIGHT)

        ctrlbar.SetVMargin(1, 1)
        self.SetControlBar(ctrlbar)
        self.SetWindow(self._list)

    def DoCommit(self):
        """Commit the selected files"""
        self._list.CommitSelectedFiles()

    def DoRevert(self):
        """Revert the selected files"""
        self._list.RevertSelectedFiles()

    def DoStatusRefresh(self):
        """Refresh the status of the currently selected repository"""
        path = self._repos[self._crepo]
        self._list.UpdatePathStatus(path)

    def DoUpdate(self):
        """Update the current repisitory"""
        path = self._repos[self._crepo]
        self._list.UpdateRepository(path)

    def EnableCommandBar(self, enable=True):
        """Enable or disable the command bar
        @keyword enable: bool

        """
        self.GetControlBar().Enable(enable)

    def FindRepos(self, path_list):
        """Find the top level source repositories under the given list
        of paths.
        @param path_list: list of strings
        @return: list

        """
        rlist = list()
        for path in path_list:
            # Only check existing paths and directories
            if not os.path.exists(path) or not os.path.isdir(path):
                continue

            scsys = self._ctrl.GetSCSystem(path)

            # If the top level project directory is not under source control
            # check the directories one level down to see if they are.
            if scsys is None:
                dirs = [ os.path.join(path, dname)
                         for dname in os.listdir(path)
                         if os.path.isdir(os.path.join(path, dname)) ]

                for dname in dirs:
                    if self._ctrl.GetSCSystem(dname) is not None:
                        rlist.append(dname)
            else:
                rlist.append(path)

        return rlist

    def SetFileOpenerHook(self, meth):
        """Set the hook method for handling when items are activated in the
        list. The callable should accept a file path string as an argument.
        @param meth: callable

        """
        self._list.SetFileOpenerHook(meth)

    def OnChoice(self, evt):
        """Handle changes in selection of the current repo"""
        if evt.GetId() == ID_REPO_CHOICE:
            self._crepo = self._repo_ch.GetSelection()
            self._repo_ch.SetToolTipString(self._repos[self._crepo])
            self.DoStatusRefresh()
        else:
            evt.Skip()

    def OnUpdateUI(self, evt):
        """Update UI of buttons based on state of list
        @param evt: wx.UpdateUIEvent
        @note: wish there was access to the wx.Window.Enable virtual method
               so that the overridden method would be called.

        """
        e_id = evt.GetId()
        if e_id in (ID_REVERT, ID_COMMIT):
            evt.Enable(self._list.GetSelectedItemCount())
        elif e_id == ID_REPO_CHOICE:
            evt.Enable(self._repo_ch.GetCount())
        elif e_id == wx.ID_REFRESH:
            evt.Enable(len(self._repo_ch.GetStringSelection()))
        else:
            evt.Skip()

#--------------------------------------------------------------------------#

class RepoModList(wx.ListCtrl,
                  elistmix.ListRowHighlighter,
                  listmix.ListCtrlAutoWidthMixin):
    """List for managing and listing files under SourceControl.
    Specifically it displays the summary of modified files under a given
    repository.

    """
    STATUS_COL = 0
    FILENAME_COL = 1
    def __init__(self, parent, id=wx.ID_ANY):
        """Create the list control"""
        wx.ListCtrl.__init__(self, parent, id,
                             style=wx.LC_REPORT | wx.LC_VRULES | wx.BORDER)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        elistmix.ListRowHighlighter.__init__(self)

        # Attributes
        self._menu = None
        self._items = list()
        self._path = None
        self._busy = False
        self._ctrl = ScCommand.SourceController(self)
        
        # Interface attributes
        self.fileHook = None

        # Setup
        self.InsertColumn(RepoModList.STATUS_COL, _("Status"),
                          wx.LIST_FORMAT_CENTER)
        self.InsertColumn(RepoModList.FILENAME_COL, _("Filename"))

        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_MENU, self.OnMenu)
        self.Bind(ScCommand.EVT_STATUS, self.OnStatus)
        self.Bind(ScCommand.EVT_CMD_COMPLETE, self.OnCommandComplete)

    def __ConstructNodes(self):
        """Make the node's list from the selected list items
        @return: list of tuples

        """
        paths = self.GetSelectedPaths()
        nodes = [(None, {'path' : path}) for path in paths]
        return nodes

    def AddFile(self, status, fname):
        """Add a file to the list
        @param status: Status indicator
        @param fname: File name

        """
        self._items.append(dict(status=status, fname=fname))
        self.Append((status, fname))

    def DeleteAllItems(self):
        """Clear the list"""
        for item in range(len(self._items)):
            self._items.pop()
        wx.ListCtrl.DeleteAllItems(self)

    def DoDiff(self):
        """Open the diff between the selected file and its previous version."""
        paths = self.GetSelectedPaths()

        for path in paths:
            # Only do files
            if os.path.isdir(path):
                # TODO: prompt that this cant be done?
                continue

            # Run the actual Diff job
            self._ctrl.CompareRevisions(path)

    def CommitSelectedFiles(self):
        """Commit the selected files"""
        paths = self.GetSelectedPaths()
        if not len(paths):
            return

        nodes = self.__ConstructNodes()
        message = u""

        # Make sure a commit message is entered
        while True:
            ted = ProjCmnDlg.CommitDialog(self, _("Commit Dialog"),
                                          _("Enter your commit message:"),
                                          paths)

            if ted.ShowModal() == wx.ID_OK:
                message = ted.GetValue().strip()
            else:
                return

            ted.Destroy()
            if message:
                break

        self._ctrl.ScCommand(nodes, 'commit', None, message=message)

    def GetSelectedPaths(self):
        """Get the paths of the selected items
        @return: list of strings

        """
        items = list()
        idx = -1
        while True:
            item = self.GetNextItem(idx, state=wx.LIST_STATE_SELECTED)
            if item == wx.NOT_FOUND:
                break
            else:
                items.append(item)
                idx = item

        paths = list()
        for idx in items:
            item = self.GetItem(idx, RepoModList.FILENAME_COL)
            path = item.GetText()
            if path:
                paths.append(path)

        return paths

    def RefreshStatus(self):
        """Refresh the screen with the latest status info from the
        current repository.
        @postcondition: status of current files in repository is refreshed and
                        displayed in the list.

        """
        self.DeleteAllItems()
        if self._path is not None:
            self.UpdatePathStatus(self._path)

    def RevertSelectedFiles(self):
        """Revert the selected files
        @postcondition: selected items in the list are reverted to the
                        repository version.

        """
        nodes = self.__ConstructNodes()
        if not len(nodes):
            return

        self.SetCommandRunning(True)
        self._ctrl.ScCommand(nodes, 'revert')

    def SetCommandRunning(self, running=True):
        """Set whether a commadn is running or not
        @keyword running: bool

        """
        self._busy = running
        self.GetParent().EnableCommandBar(not running)
        fid = self.GetTopLevelParent().GetId()
        state = (fid, 0, 0)
        if running:
            state = (fid, -1, -1)
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (fid, True))
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_STATE, state)
        else:
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (fid, False))

    def SetFileOpenerHook(self, meth):
        """Set the file opener method hook.
        @param meth: callable (def fhook(path))

        """
        if not callable(meth):
            raise ValueError("meth must be callable")

        self.fileHook = meth

    def ShowRevisionHistory(self):
        """Show the revision history for the selected files
        @postcondition: History dialog is shown for each selected file

        """
        paths = self.GetSelectedPaths()
        pos = wx.DefaultPosition
        win = None

        for path in paths:
            if win is not None:
                pos = win.GetPosition()
                pos = (pos[0] + 22, pos[1] + 22)

            # Log lookup and ScCommands are handled by HistoryWindow
            win = HistoryWindow(self, path, None, dict(path=path))
            win.Show()
            if pos != wx.DefaultPosition:
                win.SetPosition(pos)

    def UpdatePathStatus(self, path):
        """Run an status update job
        @param path: path to check status on

        """
        self.SetCommandRunning(True)
        src_c = self._ctrl.GetSCSystem(path)
        if src_c is not None:
            self._path = path
            t = threading.Thread(target=self._ctrl.StatusWithTimeout,
                                 args=(src_c, None, dict(path=path)),
                                 kwargs=dict(recursive=True))
            t.start()

    def UpdateRepository(self, path):
        """Update the repository
        @param path: repository path

        """
        self.SetCommandRunning(True)
        self._ctrl.ScCommand([(None, {'path' : path})], 'update')

    #---- Event Handlers ----#

    def OnActivated(self, evt):
        """Open the file in the editor when it is activated in the list"""
        if self.fileHook is not None:
            for path in self.GetSelectedPaths():
                self.fileHook(path)
        else:
            evt.Skip()

    def OnCommandComplete(self, evt):
        """Handle when a source control command has completed."""
#        print evt.GetValue()
#        print evt.GetError()
        self.RefreshStatus()
        self.SetCommandRunning(False)

    def OnContextMenu(self, evt):
        """Show the context menu"""
        if not self.GetSelectedItemCount() or self._busy:
            evt.Skip()
            return

        if self._menu is None:
            # Create the menu once
            self._menu = wx.Menu()
            item = self._menu.Append(wx.ID_REFRESH, _("Refresh status"))
            item.SetBitmap(FileIcons.getScStatusBitmap())
            item = self._menu.Append(ID_COMPARE_TO_PREVIOUS,
                                     _("Compare to previous version"))
            item.SetBitmap(FileIcons.getScDiffBitmap())
            item = self._menu.Append(ID_REVISION_HIST,
                                     _("Show revision history"))
            item.SetBitmap(FileIcons.getScHistoryBitmap())
            item = self._menu.Append(ID_COMMIT, _("Commit changes"))
            item.SetBitmap(FileIcons.getScCommitBitmap())
            item = self._menu.Append(ID_REVERT,
                                     _("Revert to repository version"))
            item.SetBitmap(FileIcons.getScRevertBitmap())

        self.PopupMenu(self._menu)

    def OnMenu(self, evt):
        """Handler for menu events from context menu"""
        e_id = evt.GetId()
        if e_id == ID_COMPARE_TO_PREVIOUS:
            # Do Diff
            self.DoDiff()
        elif e_id == ID_COMMIT:
            # Checkin
            self.CommitSelectedFiles()
        elif e_id == ID_REVERT:
            # Revert changes
            self.RevertSelectedFiles()
        elif e_id == ID_REVISION_HIST:
            # Show the history of the selected file
            self.ShowRevisionHistory()
        elif e_id == wx.ID_REFRESH:
            # Refresh the status
            self.RefreshStatus()
        else:
            evt.Skip()

    def OnStatus(self, evt):
        """Handler for the status command event. Updates the list with
        the status of the files from the selected repository.

        """
        status = evt.GetValue()[1:]

        path = None
        if len(status):
            path = status[0].get('path', None)
            status = status[1]

        if path is None:
            # TODO: notify that the status check failed?
            return

        # Clear the display
        self.DeleteAllItems()

        # Update the display
        for fname, stat in status.iteritems():
            fstatus = stat.get('status', 'uptodate')
            if fstatus != 'uptodate':
                self.AddFile(STATUS.get(fstatus, u'U'),
                             os.path.join(path, fname))

        self.SetCommandRunning(False)
