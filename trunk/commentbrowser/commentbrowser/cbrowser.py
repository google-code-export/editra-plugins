#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#Name: cbrowser.py                                                           #
#Purpose: UI portion of the CommentBrowser Plugin                            #
#Author: DR0ID <dr0iddr0id@googlemail.com>                                   #
#Copyright: (c) 2008 DR0ID                                                   #
#Licence: wxWindows Licence                                                  #
###############################################################################

"""
Provides a comment browser panel and other UI components for Editra's
CommentBrowser Plugin.

"""

__author__ = 'DR0ID <dr0iddr0id@googlemail.com>'
__svnid__ = '$Id: browser.py 50827 2007-12-19 08:48:03Z CJP $'
__revision__ = '$Revision$'

#-----------------------------------------------------------------------------#
#Imports

import os.path
import re
import wx

#Editra Library Modules

import ed_glob
import syntax
from extern import flatnotebook as FNB

#Local

from cbrowserlistctrl import TestListCtrl

#--------------------------------------------------------------------------#
#Globals

_ = wx.GetTranslation

PANE_NAME = u'CommentBrowser'
CAPTION = _(u'Comment Browser')
ID_CBROWSERPANE = wx.NewId()
ID_COMMENTBROWSE = wx.NewId()  #menu item
ID_TIMER = wx.NewId()

#[low priority, ..., high priority]

TASK_CHOICES = [_('ALL'), _('TODO'), _('HACK'), _('XXX'), _('FIXME')]

RE_TASK_CHOICES = []
for task in TASK_CHOICES:
    expr = r"""(?i)""" + task + r"""\s*:(.*$)"""
    RE_TASK_CHOICES.append(re.compile(expr, re.UNICODE))

#--------------------------------------------------------------------------#

#TODO: better comments
#TODO: change to use new message system instead of the events
#TODO: remove selection of a listitem when sorting
#TODO: save pane position in config?



class CBrowserPane(wx.Panel):

    """Creates a Commentbrowser panel"""

    def __init__(
        self,
        parent,
        id,
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=wx.NO_BORDER,
        ):
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

        self._mainwin = parent
        self.__log = wx.GetApp().GetLog()

        self._timer = wx.Timer(self, ID_TIMER)
        self._intervall = 500  # milli seconds

        #---- Add Menu Items ----#

        viewm = self._mainwin.GetMenuBar().GetMenuByName('view')
        self._mi = viewm.InsertAlpha(ID_COMMENTBROWSE, CAPTION,
                                     _('Open Comment Browser Sidepanel'),
                                     wx.ITEM_CHECK, after=ed_glob.ID_PRE_MARK)
        self._mi.Check(False)
        if self.IsShown():
            self._mi.Check(True)

        #---- Gui ----#

        self._listctrl = TestListCtrl(self)

        self._taskChoices = TASK_CHOICES
        self._taskFilter = wx.Choice(self, choices=self._taskChoices)
        self._taskFilter.SetStringSelection(self._taskChoices[0])
        self._checkBoxAllFiles = wx.CheckBox(self, label=_('All opened files'),
                 style=wx.ALIGN_LEFT)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        tasklbl = wx.StaticText(self, label=_('Taskfilter: '))
        hsizer.Add((5, 5))
        hsizer.Add(tasklbl, 0, wx.ALIGN_CENTER_VERTICAL)
        hsizer.Add((5, 5))
        hsizer.Add(self._taskFilter, 0, wx.ALIGN_CENTER_VERTICAL)
        hsizer.Add((-1, 5), 1, wx.EXPAND)
        hsizer.Add(self._checkBoxAllFiles, 0, wx.ALIGN_CENTER_VERTICAL
                    | wx.ALIGN_RIGHT)
        hsizer.Add((5, 5))

        btn = wx.Button(self, label=_('Update'))
        hsizer.Add(btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        hsizer.Add((5, 5))

        #Use small version of controls on osx as they are more suitable in this
        #use case.
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

        self.Bind(wx.EVT_TIMER, self.OnListUpdate, self._timer)

        btn.Bind(wx.EVT_BUTTON, self.OnListUpdate, btn)
        self._taskFilter.Bind(wx.EVT_CHOICE, self.OnListUpdate,
                              self._taskFilter)

        self._mainwin.GetNotebook().Bind(FNB.EVT_FLATNOTEBOOK_PAGE_CLOSED,
                self.OnPageClose, self._mainwin.GetNotebook())
        self._mainwin.GetNotebook().Bind(FNB.EVT_FLATNOTEBOOK_PAGE_CHANGED,
                self.OnPageChange, self._mainwin.GetNotebook())

        self._checkBoxAllFiles.Bind(wx.EVT_CHECKBOX, self.OnCheckAll,
                                    self._checkBoxAllFiles)
        self._mainwin.GetFrameManager().Bind(wx.aui.EVT_AUI_PANE_CLOSE,
                self.OnPaneClose)

    #---- Private Methods ----#

    def _log(self, msg):
        """
        writes a log message to the app log
        @param msg: message to write to the log
        """

        self.__log('[commentbrowser] ' + str(msg))

    def __del__(self):
        """
        stops the timer when the object gets deleted if it is still running
        """
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

            if textctrl is not None and getattr(textctrl, '__name__', '')\
                 == 'EditraTextCtrl':
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
#                                taskdict[hash(taskentry)] = taskentry
                                taskdict[self.__getNewKey()] = taskentry
        self._listctrl.ClearEntries()
        self._listctrl.AddEntries(taskdict)
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

    def OnCheckAll(self, event):
        """
        Callback if the checkbox is un-/checked.
        @param event: wxEvent
        """
        self.UpdateCurrent()
        
    def OnKey(self, event):
        """
        Callback when keys are pressed in the current textctrl.
        @param event: wxEvent
        """
        self._timer.Start(self._intervall, True)
        event.Skip()

    def OnListUpdate(self, event):
        """
        Callback if EVT_TIMER, EVT_BUTTON or EVT_CHOICE is fired.
        @param event: wxEvent
        """

        #called on: EVT_TIMER, EVT_BUTTON, EVT_CHOICE

        self.UpdateCurrent()

    def OnPageChange(self, event):
        """
        Callback when a page is changed in the notebook
        @param event: wxEvent
        """
        #Need to skip event right away to let page change properly

        event.Skip()

        #ed_pages updates the GetCurrentCtrl() after processing OnPageChanged
        #that is why I have to grab the ctrl this way

        ctrl = self._mainwin.GetNotebook().GetPage(event.GetSelection())
        self.UpdateCurrent(ctrl)
#        ctrl.Bind(wx.EVT_CHAR, self.OnKey)
        ctrl.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        # only sort if it lists the tasks only for one file
        if not self._checkBoxAllFiles.GetValue():
            self._listctrl.SortListItems(0, 0)

    def OnPageClose(self, event):
        """
        Callback when a page is closed.
        @param event: wxEvent
        """

        #Need to skip event right away to let notebook to finish processing
        #ed_pages updates the GetCurrentCtrl() after processing OnPageChanged
        #that is why I have to grab the ctrl this way

        event.Skip()
        ctrl = self._mainwin.GetNotebook().GetPage(event.GetSelection())
        self.UpdateCurrent(ctrl)

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
                self._mi.Check(False)
            else:
                pane.Show()
                self._mi.Check(True)
            mgr.Update()
        else:
            evt.Skip()

    def OnPaneClose(self, evt):
        """
        Clean up settings when Comment Browser Pane is closed
        @param event: wxEvent
        """

        paneName = evt.GetPane().name
        if PANE_NAME == paneName:
            self._mi.Check(False)
            evt.Skip()

            #TODO: save pane position in config?

#---------------------------------------------------------------------------- #
