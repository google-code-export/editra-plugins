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
import ed_glob
import syntax
import ed_msg
import profiler
from extern import flatnotebook as FNB


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
#TODO: how to do translations of plugins?
#TODO: coloring of priorities: if all entries have same prio?

#---- examples ----#

#TODO: example todo
#Fixme: example fixme
#XXX: is this really a good idea? ;-)
#hack: all this code is hacked

#tOdO: hight priority!!!!!!!
#fixme: !important!

#---- examples ----#


class CBrowserPane(wx.Panel):

    """Creates a Commentbrowser panel"""

    def __init__(
        self,
        parent,
        id=wx.ID_ANY,
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=wx.NO_BORDER,
        menu=None):
        """ Initializes the CBrowserPane class"""

        wx.Panel.__init__(
            self,
            parent,
            id,
            pos,
            size,
            style,
            )

        #---- private attr ----#

        self._mainwin = self.__FindMainWindow()
        self._mi = menu
        self.__log = wx.GetApp().GetLog()

        self._timer = wx.Timer(self, ID_TIMER)
        self._intervall = 500  # milli seconds

        #---- Gui ----#

        self._listctrl = CustomListCtrl(self)

        self._taskChoices = TASK_CHOICES
        self._taskFilter = wx.Choice(self, choices=self._taskChoices)
        self._taskFilter.SetStringSelection(self._taskChoices[0])
        self._checkBoxAllFiles = wx.CheckBox(self, label=_('All opened files'),
                 style=wx.ALIGN_LEFT)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        tasklbl = wx.StaticText(self, label=_('Taskfilter: '))
        btn = wx.Button(self, label=_('Update'))
        hsizer.AddMany([((5, 5)), (tasklbl, 0, wx.ALIGN_CENTER_VERTICAL),
                        ((5, 5)), (self._taskFilter, 0, wx.ALIGN_CENTER_VERTICAL),
                        ((-1, 5), 1, wx.EXPAND),
                        (self._checkBoxAllFiles, 0, wx.ALIGN_CENTER_VERTICAL |\
                                                    wx.ALIGN_RIGHT),
                        ((5, 5)),
                        (btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT),
                        ((5, 5))])

        # Use small version of controls on osx
        if wx.Platform == '__WXMAC__':
            for win in [self._taskFilter, tasklbl, btn,
                        self._checkBoxAllFiles]:
                win.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(hsizer, 0, wx.EXPAND)
        sizer.Add(self._listctrl, 1, wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.Layout()

        #---- Bind events ----#

        self._mainwin.Bind(wx.EVT_ACTIVATE, self.OnActivate)
        self.Bind(wx.EVT_TIMER, lambda evt: self.UpdateCurrent(), self._timer)
        self.Bind(wx.EVT_BUTTON, lambda evt: self.UpdateCurrent(), btn)
        self.Bind(wx.EVT_CHOICE, lambda evt: self.UpdateCurrent(), self._taskFilter)

        # Main notebook events
        ed_msg.Subscribe(self.OnPageClose, ed_msg.EDMSG_UI_NB_CLOSED)
        ed_msg.Subscribe(self.OnPageChange, ed_msg.EDMSG_UI_NB_CHANGED)

        self.Bind(wx.EVT_CHECKBOX, lambda evt: self.UpdateCurrent(), self._checkBoxAllFiles)

        # Only bind this event when the pane is using the mainwindow interface
        if self.GetId() == ID_CBROWSERPANE:
            self._mainwin.GetFrameManager().Bind(wx.aui.EVT_AUI_PANE_CLOSE,
                                                 self.OnPaneClose)

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
            return getattr(tlw, '__name__', '') == 'MainWindow'

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
        super(CBrowserPane, self).__del__()

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
                    self._log('[error]:' + str(excp.message))
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
                                taskentry = (
                                    int(prio),
                                    str(self._taskChoices[tasknr]),
                                    str(descr),
                                    str(filename),
                                    int(idx + 1),
                                    str(fullname),
                                    )
                                taskdict[self.__getNewKey()] = taskentry
        self._listctrl.Freeze()
        self._listctrl.ClearEntries()
        self._listctrl.AddEntries(taskdict)
        self._listctrl.Thaw()
        self._listctrl.SortItems() # SortItems() calls Refresh()
        
    def __getNewKey(self):
        """
        key generator method for the list entries
        @returns: integer
        """
        z = 0
        while 1:
            yield z
            z += 1

    def IsComment(self, stc, bufferpos):
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

            #python is special: look if its is in a documentation string

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
        self.UpdateCurrent()

    def OnPageChange(self, msg):
        """
        Callback when a page is changed in the notebook
        @param event: Message Object (notebook, current page)

        """
        # Get the Current Control
        nb, page = msg.GetData()
        ctrl = nb.GetPage(page)
        self.UpdateCurrent(ctrl)

        # only sort if it lists the tasks only for one file
        if not self._checkBoxAllFiles.GetValue():
            self._listctrl.SortListItems(0, 0)

    def OnPageClose(self, msg):
        """
        Callback when a page is closed.
        @param event: Message Object (notebook, page index)

        """
        nb, page = msg.GetData()
        if nb.GetPageCount() < page:
            ctrl = nb.GetPage(page)
            wx.CallAfter(self.UpdateCurrent, ctrl)

    def OnActivate(self, event):
        """
        Callback when app goes to sleep or awakes.
        @param event: wxEvent
        """
        if event.GetActive():
            pass
            #awake, reastart timer
#            self.UpdateCurrent()
        else:
            pass
            #going to sleep
        event.Skip()

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

    def UpdateMenuItem(self, evt):
        """Update the check mark for the menu item"""
        mgr = self._mainwin.GetFrameManager()
        pane = mgr.GetPane(self.PANE_NAME)
        self._mi.Check(pane.IsShown())
        evt.Skip()

    def OnPaneClose(self, evt):
        """
        Clean up settings when Comment Browser Pane is closed
        @param event: wxEvent

        """
        pane = evt.GetPane()
        paneName = pane.name
        if PANE_NAME == paneName and pane.window.GetId() == ID_CBROWSERPANE:
            self._mi.Check(False)
        evt.Skip()

        #TODO: save pane position in config?

#---------------------------------------------------------------------------- #
