#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#Name: cbrowser.py                                                           #
#Purpose: UI portion of the CommentBrowser Plugin                            #
#Author: DR0ID <dr0iddr0id@googlemail.com>                                   #
#Copyright: (c) 2008 DR0ID                                                   #
#License: wxWindows License                                                  #
###############################################################################

"""
Provides a comment browser panel and other UI components for Editra's
CommentBrowser Plugin.

"""

__author__ = 'DR0ID <dr0iddr0id@googlemail.com>'
__svnid__ = '$Id: browser.py 50827 2007-12-19 08:48:03Z CJP $'
__revision__ = '$Revision$'

#-----------------------------------------------------------------------------#
# Imports
import os.path
import re
import wx

# Editra Library Modules
import syntax
import ed_msg
import profiler
import eclib.ctrlbox as ctrlbox


# Local
from cbrowserlistctrl import CustomListCtrl

#--------------------------------------------------------------------------#
#Globals

_ = wx.GetTranslation

# Identifiers
PANE_NAME = 'CommentBrowser'
CAPTION = _('Comment Browser')
CB_KEY = 'CommentBrowser.Show'
ID_CBROWSERPANE = wx.NewId()
ID_COMMENTBROWSE = wx.NewId()  #menu item
ID_CB_SHELF = wx.NewId() # Shelf interface id
ID_TIMER = wx.NewId()

#[low priority, ..., high priority]

TASK_CHOICES = ['ALL', 'NOTE', 'TODO', 'HACK', 'XXX', 'FIXME']

RE_TASK_CHOICES = []
for task in TASK_CHOICES:
    expr = r"""(?i)""" + task + r"""\s*:(.*$)"""
    RE_TASK_CHOICES.append(re.compile(expr, re.UNICODE))

#--------------------------------------------------------------------------#

#TODO: remove selection of a listitem when sorting
#TODO: save pane position in config?

#---- examples ----#

#TODO: example todo
#Fixme: example fixme
#XXX: is this really a good idea? ;-)
#hack: all this code is hacked

#tOdO: hight priority!!!!!!!
#fixme: !important!

#---- examples ----#


class CBrowserPane(ctrlbox.ControlBox):
    """Creates a Commentbrowser panel"""
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.NO_BORDER, menu=None):
        """ Initializes the CBrowserPane class"""
        ctrlbox.ControlBox.__init__(self, parent, id, pos, size, style)

        #---- private attr ----#

        self._mainwin = self.__FindMainWindow()
        self._mi = menu
        self.__log = wx.GetApp().GetLog()

        self._timer = wx.Timer(self, ID_TIMER)
        self._intervall = 500  # milli seconds

        self._taskChoices = TASK_CHOICES

        #---- Gui ----#

        ctrlbar = ctrlbox.ControlBar(self, style=ctrlbox.CTRLBAR_STYLE_GRADIENT)
        if wx.Platform == '__WXGTK__':
            ctrlbar.SetWindowStyle(ctrlbox.CTRLBAR_STYLE_DEFAULT)

        self.SetControlBar(ctrlbar)
        self._listctrl = CustomListCtrl(self)
        self.SetWindow(self._listctrl)

        tasklbl = wx.StaticText(ctrlbar, label=_('Taskfilter: '))
        ctrlbar.AddControl(tasklbl, wx.ALIGN_LEFT)
        self._taskFilter = wx.Choice(ctrlbar, choices=self._taskChoices)
        self._taskFilter.SetStringSelection(self._taskChoices[0])
        ctrlbar.AddControl(self._taskFilter, wx.ALIGN_LEFT)
        ctrlbar.AddStretchSpacer()
        self._checkBoxAllFiles = wx.CheckBox(ctrlbar,
                                             label=_('All opened files'))
        ctrlbar.AddControl(self._checkBoxAllFiles, wx.ALIGN_RIGHT)
        self._chekcBoxAfterKey = wx.CheckBox(ctrlbar, label=_('After key'))
        self._chekcBoxAfterKey.SetToolTipString(_("Update as you type"))
        ctrlbar.AddControl(self._chekcBoxAfterKey, wx.ALIGN_RIGHT)
        btn = wx.Button(ctrlbar, label=_('Update'))
        ctrlbar.AddControl(btn, wx.ALIGN_RIGHT)

        #---- Bind events ----#

        self.Bind(wx.EVT_TIMER, lambda evt: self.UpdateCurrent(), self._timer)
        self.Bind(wx.EVT_BUTTON, lambda evt: self.UpdateCurrent(), btn)
        self.Bind(wx.EVT_CHOICE,
                  lambda evt: self.UpdateCurrent(), self._taskFilter)

        # Main notebook events
        ed_msg.Subscribe(self.OnPageClose, ed_msg.EDMSG_UI_NB_CLOSED)
        ed_msg.Subscribe(self.OnPageChange, ed_msg.EDMSG_UI_NB_CHANGED)

        self.Bind(wx.EVT_CHECKBOX,
                  lambda evt: self.UpdateCurrent(),
                  self._checkBoxAllFiles)

        # File action messages
        ed_msg.Subscribe(self.OnListUpdate, ed_msg.EDMSG_FILE_SAVED)
        ed_msg.Subscribe(self.OnListUpdate, ed_msg.EDMSG_FILE_OPENED)
        ed_msg.Subscribe(self.OnKey, ed_msg.EDMSG_UI_STC_KEYUP)

    #---- Private Methods ----#

    def __FindMainWindow(self):
        """Find the mainwindow of this control. The mainwindow will either be
        the Top Level Window or if the panel is undocked it will be the parent
        of the miniframe the panel is in.
        @return: MainWindow or None

        """
        def IsMainWin(win):
            """Is the window a mainwindow"""
            return getattr(win, '__name__', '') == 'MainWindow'

        tlw = self.GetTopLevelParent()
        if IsMainWin(tlw):
            return tlw
        elif hasattr(tlw, 'GetParent'):
            tlw = tlw.GetParent()
            if IsMainWin(tlw):
                return tlw

        return None

    def _log(self, msg):
        """
        Writes a log message to the app log
        @param msg: message to write to the log

        """
        self.__log('[commentbrowser] ' + str(msg))

    def __del__(self):
        """
        Stops the timer when the object gets deleted if it is still running

        """
        ed_msg.Unsubscribe(self.OnListUpdate)
        ed_msg.Unsubscribe(self.OnKey)
        ed_msg.Unsubscribe(self.OnPageClose)
        ed_msg.Unsubscribe(self.OnPageChange)
        self._log('__del__(): stopping timer')
        self._timer.Stop()

    #---- Methods ----#

    def UpdateCurrent(self, intextctrl=None):
        """
        Updates the entries of the current page in the todo list.
        If textctrl is None then it trys to use the current page,
        otherwise it trys to use the passed in textctrl.
        @param intextctrl: textctrl to update (should be of type ed_stc)
        """
        # stop the timer if it is running
        if self._timer.IsRunning():
            self._timer.Stop()

        controls = []
        if self._checkBoxAllFiles.GetValue():
            controls.extend(self._mainwin.GetNotebook().GetTextControls())
        else:
            if intextctrl is None:
                controls = [self._mainwin.GetNotebook().GetCurrentCtrl()]
            else:
                controls = [intextctrl]
        taskdict = {}

        for textctrl in controls:

            #make sure it is a text ctrl

            if textctrl is not None and \
               getattr(textctrl, '__name__', '') == 'EditraTextCtrl':
                try:
                    fullname = textctrl.GetFileName()
                    filename = os.path.split(fullname)[1]
                    textlines = textctrl.GetText().splitlines()
                except Exception, excp:
                    self._log('[error] ' + str(excp.message))
                    self._log(type(excp))
                    return

                filterVal = self._taskFilter.GetStringSelection()
                choice = self._taskChoices.index(filterVal)

                for (idx, line) in enumerate(textlines):

                    #search for the tasks

                    for tasknr in range(1, len(self._taskChoices)):

                        #tasknr: meaning is the order of the self._taskChoices

                        todo_hit = RE_TASK_CHOICES[tasknr].search(line)
                        if todo_hit:
                            if (choice == 0 or choice == tasknr) and todo_hit\
                                 and self.IsComment(textctrl,
                                    textctrl.PositionFromLine(idx)
                                     + todo_hit.start(1)):

                                descr = todo_hit.group(1).strip()
                                prio = descr.count('!')

                                #prio is higher if further in the list
                                prio += tasknr
                                taskentry = (int(prio),
                                             str(self._taskChoices[tasknr]),
                                             descr, filename, int(idx + 1),
                                             fullname)
                                taskdict[self.__getNewKey()] = taskentry

        # Update the list
        self._listctrl.Freeze()
        self._listctrl.ClearEntries()
        self._listctrl.AddEntries(taskdict)
        self._listctrl.Thaw()
        self._listctrl.SortItems() # SortItems() calls Refresh()

    @staticmethod
    def __getNewKey():
        """
        key generator method for the list entries
        @returns: integer

        """
        z = 0
        while 1:
            yield z
            z += 1

    def GetMainWindow(self):
        """
        Get them main window that owns this instance

        """
        return self._mainwin

    def IsActive(self):
        """Check whether this browser is active or not"""
        return self._mainwin.IsActive()

    @staticmethod
    def IsComment(stc, bufferpos):
        """
        Check whether the given point in the buffer is a comment
        region or not (special case python: it returns also True if the region
        is a documentation string, using triple quotes).
        @param stc: an EdStc object
        @param bufferpos: Zero based index of position in the buffer to check

        """

        style_id = stc.GetStyleAt(bufferpos)
        style_tag = stc.FindTagById(style_id)
        if 'comment' in style_tag.lower():
            return True
        else:

            # Python is special: look if its is in a documentation string

            if stc.GetLangId() == syntax.synglob.ID_LANG_PYTHON:
                if wx.stc.STC_P_TRIPLEDOUBLE == style_id or wx.stc.STC_P_TRIPLE\
                     == style_id:
                    return True
            return False

    #---- Eventhandler ----#

    def OnKey(self, msg):
        """
        Callback when keys are pressed in the current textctrl.
        @param event: Message Object ((x, y), keycode)

        """
        if not self.IsActive() or not self._chekcBoxAfterKey.GetValue():
            return

#        self._log('OnKey')
        # Don't update on meta key events
        data = msg.GetData()
        if data[1] not in [wx.WXK_SHIFT, wx.WXK_COMMAND, wx.WXK_CONTROL,
                            wx.WXK_ALT, wx.WXK_TAB]:
            self._timer.Start(self._intervall, True)

    def OnListUpdate(self, event):
        """
        Callback if EVT_TIMER, EVT_BUTTON or EVT_CHOICE is fired.
        @param event: wxEvent

        """
        #called on: ed_msg.EDMSG_FILE_SAVED
#        self._log('OnListUpdate')
        if not self.IsActive():
            return

        self.UpdateCurrent()

    def OnPageChange(self, msg):
        """
        Callback when a page is changed in the notebook
        @param event: Message Object (notebook, current page)

        """
        if not self.IsActive():
            return

        # Get the Current Control
        nbook, page = msg.GetData()
        ctrl = nbook.GetPage(page)
        self.UpdateCurrent(ctrl)

        # only sort if it lists the tasks only for one file
        if not self._checkBoxAllFiles.GetValue():
            self._listctrl.SortListItems(0, 0)

    def OnPageClose(self, msg):
        """
        Callback when a page is closed.
        @param event: Message Object (notebook, page index)

        """
        if not self.IsActive():
            return

        nbook, page = msg.GetData()
        if nbook.GetPageCount() < page:
            ctrl = nbook.GetPage(page)
            wx.CallAfter(self.UpdateCurrent, ctrl)

    def OnShow(self, evt):
        """
        Shows the Comment Browser
        @param event: wxEvent

        """
        if evt.GetId() == ID_COMMENTBROWSE:
            mgr = self._mainwin.GetFrameManager()
            pane = mgr.GetPane(PANE_NAME)
            if pane.IsShown():
                pane.Hide()
                profiler.Profile_Set(CB_KEY, False)
            else:
                pane.Show()
                profiler.Profile_Set(CB_KEY, True)
            mgr.Update()
        else:
            evt.Skip()

    def OnUpdateMenu(self, evt):
        """UpdateUI handler for the panels menu item, to update the check
        mark.
        @param evt: wx.UpdateUIEvent

        """
        pane = self._mainwin.GetFrameManager().GetPane(PANE_NAME)
        evt.Check(pane.IsShown())

#---------------------------------------------------------------------------- #
