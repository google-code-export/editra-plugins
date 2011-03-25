# -*- coding: utf-8 -*-
###############################################################################
# Name: ToolConfig.py                                                         #
# Purpose: Python Configuration Panel                                         #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2010 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""PyTools Configuration User Interface"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import wx

# Editra Libraries
from profiler import Profile_Get, Profile_Set
import eclib
import util

# Local Imports
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Debugger import RPDBDEBUGGER

#-----------------------------------------------------------------------------#
# Configuration Keys
PYTOOL_CONFIG = "PyTool.Config"
TLC_PYTHON_PATH = "PythonPath"
TLC_TRAP_EXCEPTIONS = "TrapExceptions"
TLC_SYNCHRONICITY = "Synchronicity"
TLC_AUTO_FORK = "AutoFork"
TLC_FORK_MODE = "ForkMode"
TLC_EXECEVALENCODING = "ExecEvalEncoding"
TLC_EXECEVALESCAPING = "ExecEvalEscaping"
TLC_LINT_AUTORUN = "LintAutoRun"
TLC_DISABLED_CHK = "DisabledCheckers"
TLC_BREAKPOINTS = "Breakpoints"
TLC_EXPRESSIONS = "Expressions"

# Globals
_ = wx.GetTranslation
NOPYTHONERROR = u"***  FATAL ERROR: No local Python configured or found"

#-----------------------------------------------------------------------------#

def GetConfigValue(key):
    """Get a value from the config"""
    config = Profile_Get(PYTOOL_CONFIG, default=dict())
    return config.get(key, None)

def GetPythonExecutablePath(info):
    # Figure out what Python to use
    # 1) First check configuration
    # 2) Second check for it on the path
    localpythonpath = GetConfigValue(TLC_PYTHON_PATH)
    if not localpythonpath:
        localpythonpath = PyToolsUtils.GetDefaultPython()

    if localpythonpath:
        util.Log("[%s][info] Using Python: %s" % (info, localpythonpath))
        return (True, localpythonpath)
    else:
        # No configured Python
        util.Log("[%s][info] %s" % (info, NOPYTHONERROR))
        return (False, NOPYTHONERROR)

#-----------------------------------------------------------------------------#

class ToolConfigDialog(eclib.ECBaseDlg):
    """Standalone configuraton dialog"""
    def __init__(self, parent):
        super(ToolConfigDialog, self).__init__(parent, title=_("PyTools Config"),
                                               style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        # Setup
        self.SetPanel(ToolConfigPanel(self))
        self.SetInitialSize()

#-----------------------------------------------------------------------------#

class ToolConfigPanel(wx.Panel):
    def __init__(self, parent):
        super(ToolConfigPanel, self).__init__(parent)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(ConfigBook(self), 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(sizer)

#-----------------------------------------------------------------------------#

class ConfigBook(wx.Notebook):
    """Notebook to hold all the configuration panels"""
    def __init__(self, parent):
        super(ConfigBook, self).__init__(parent)

        # Attributes
        self._general = GeneralConfigPanel(self)
        self._debug = DebugConfigPanel(self)
        self._lint = LintConfigPanel(self)

        # Setup
        self.AddPage(self._general, _("General"))
        self.AddPage(self._debug, _("Debugger"))
        self.AddPage(self._lint, _("PyLint"))

#-----------------------------------------------------------------------------#

class GeneralConfigPanel(wx.Panel):
    def __init__(self, parent):
        super(GeneralConfigPanel, self).__init__(parent)

        # Attributes
        self._python_path_pk = None

        # Setup
        self.__DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnPythonPathChanged, self._python_path_pk)

    def __DoLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        config = Profile_Get(PYTOOL_CONFIG, default=dict())
        pythonpath = config.get(TLC_PYTHON_PATH, None)
        if not pythonpath:
            pythonpath = PyToolsUtils.GetDefaultPython()
        self._python_path_pk = wx.FilePickerCtrl(self, path=pythonpath,
                                                 style=wx.FLP_USE_TEXTCTRL|\
                                                       wx.FLP_CHANGE_DIR|\
                                                       wx.FLP_FILE_MUST_EXIST)
        self._python_path_pk.SetPickerCtrlGrowable(True)
        self._python_path_pk.SetToolTipString(_("Path to python executable"))
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(self, label=_("Python Path:")),
                   0, wx.ALIGN_CENTER_VERTICAL)
        hsizer.Add(self._python_path_pk, 1, wx.EXPAND|wx.ALL, 3)
        sizer.Add(hsizer, 0, wx.EXPAND|wx.ALL, 8)
        self.SetSizer(sizer)

    def OnPythonPathChanged(self, event):
        """Update the configured pylint path"""
        path = self._python_path_pk.GetPath()
        if path and os.path.exists(path):
            config = Profile_Get(PYTOOL_CONFIG, default=dict())
            config[TLC_PYTHON_PATH] = path
            Profile_Set(PYTOOL_CONFIG, config)

#-----------------------------------------------------------------------------#

class LintConfigPanel(wx.Panel):
    """Configuration panel for Python configuration in the
    PluginManager dialog.

    """
    def __init__(self, parent):
        super(LintConfigPanel, self).__init__(parent)

        # Attributes
        config = Profile_Get(PYTOOL_CONFIG, default=dict())
        modebox = wx.StaticBox(self, label=_("Lint Run Mode"))
        self._lintmodesz = wx.StaticBoxSizer(modebox, wx.VERTICAL)
        self._lintautorb = wx.RadioButton(self, label=_("Automatic"), style=wx.RB_GROUP)
        tooltip = _("Automatically rerun on save, document change, and file load")
        self._lintautorb.SetToolTipString(tooltip)
        self._lintmanualrb = wx.RadioButton(self, label=_("Manual"))
        tooltip = _("Only run when requested")
        self._lintmanualrb.SetToolTipString(tooltip)
        mode = config.get(TLC_LINT_AUTORUN, False)
        self._lintautorb.SetValue(mode)
        self._lintmanualrb.SetValue(not mode)

        ## Message configuration
        msgbox = wx.StaticBox(self, label=_("Messages"))
        self._msgsz = wx.StaticBoxSizer(msgbox, wx.VERTICAL)
        self._msgtype = wx.Choice(self, choices=_GetPyLintMessageTypes())
        self._msglst = MessageIDList(self, style=wx.LC_REPORT)

        # Setup
        self._msglst.SetConfig(config)
        self._msgtype.SetSelection(0)
        self.UpdateListCtrl()
        self.__DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_CHOICE, self.OnChoice, self._msgtype)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRunModeCheckBox, self._lintautorb)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRunModeCheckBox, self._lintmanualrb)

    def __DoLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Run mode configuration
        self._lintmodesz.Add(self._lintautorb, 0, wx.ALL, 5)
        self._lintmodesz.Add(self._lintmanualrb, 0, wx.ALL, 5)
        sizer.Add(self._lintmodesz, 0, wx.ALL|wx.EXPAND, 8)

        # Enable/Disable pylint checkers
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        typelbl = wx.StaticText(self, label=_("Message Type: "))
        hsizer.AddMany([((5, 5),0), (typelbl, 0, wx.ALIGN_CENTER_VERTICAL),
                        ((5, 5),0),
                        (self._msgtype, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND),
                        ((5, 5),0)])
        self._msgsz.Add(hsizer, 0, wx.EXPAND|wx.ALL, 5)
        self._msgsz.Add(self._msglst, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(self._msgsz, 1, wx.EXPAND|wx.ALL, 8)
        self.SetSizer(sizer)

    def OnChoice(self, evt):
        if evt.GetEventObject() is self._msgtype:
            self.UpdateListCtrl()
        else:
            evt.Skip()

    def OnRunModeCheckBox(self, evt):
        evt_obj = evt.GetEventObject()
        config = Profile_Get(PYTOOL_CONFIG, default=dict())
        if evt_obj in (self._lintautorb, self._lintmanualrb):
            config[TLC_LINT_AUTORUN] = self._lintautorb.GetValue()
        else:
            evt.Skip()
            return

        Profile_Set(PYTOOL_CONFIG, config)

    def UpdateListCtrl(self):
        """Update the list control for the selected message type"""
        if self._msglst.GetItemCount() > 0:
            self._msglst.DeleteAllItems()

        sel = self._msgtype.GetSelection()
        funct = { 0 : Conventions,
                  1 : Refactor,
                  2 : Warnings,
                  3 : Errors,
                  4 : Fatal }
        self._msglst.LoadData(funct[sel]())

#-----------------------------------------------------------------------------#

class DebugConfigPanel(wx.Panel):
    """Configuration panel for Python Debugger in the
    PluginManager dialog.

    """
    def __init__(self, parent):
        super(DebugConfigPanel, self).__init__(parent)

        # Attributes
        config = Profile_Get(PYTOOL_CONFIG, default=dict())
        self._trapcb = wx.CheckBox(self, label=_("Trap Unhandled Exceptions"))
        trap = config.get(TLC_TRAP_EXCEPTIONS, True)
        self._trapcb.SetValue(trap)
        RPDBDEBUGGER.set_trap_unhandled_exceptions(trap)

        self._synccb = wx.CheckBox(self, label=_("Allow Synchronicity"))
        synchronicity = config.get(TLC_SYNCHRONICITY, True)
        self._synccb.SetValue(synchronicity)
        RPDBDEBUGGER.set_synchronicity(synchronicity)

        self._forkcb = wx.CheckBox(self, label=_("Pause before fork"))
        autofork = config.get(TLC_AUTO_FORK, True)
        self._forkcb.SetValue(not autofork)

        self._forkchildcb = wx.CheckBox(self, label=_("Fork into Child"))
        forkmode = config.get(TLC_FORK_MODE, False)
        self._forkchildcb.SetValue(forkmode)
        RPDBDEBUGGER.set_fork_mode(forkmode, autofork)

        self._enclbl = wx.StaticText(self, label=_("Source Encoding:"))
        encodings = eclib.GetAllEncodings()
        encodings.insert(0, "auto")
        self._encch = wx.Choice(self, wx.ID_ANY, choices=encodings)
        self._encch.SetToolTipString(_("Source Encoding for Execute/Evaluate"))
        encoding = config.get(TLC_EXECEVALENCODING, "auto")
        self._encch.SetStringSelection(encoding)

        self._esccb = wx.CheckBox(self, label=_("Escape Non-Ascii Characters for Execute/Evaluate"))
        escaping = config.get(TLC_EXECEVALESCAPING, True)
        self._esccb.SetValue(escaping)
        RPDBDEBUGGER.set_encoding(encoding, escaping)

        # Layout
        self.__DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_CHECKBOX, self.OnTrapExceptionsCheckBox, self._trapcb)
        self.Bind(wx.EVT_CHECKBOX, self.OnSynchronicityCheckBox, self._synccb)
        self.Bind(wx.EVT_CHECKBOX, self.OnForkCheckBox, self._forkcb)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnForkCheckBox, self._forkchildcb)
        self.Bind(wx.EVT_CHOICE, self.OnEncoding, self._encch)
        self.Bind(wx.EVT_CHECKBOX, self.OnEscapingCheckBox, self._esccb)

    def __DoLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((10, 10), 0)

        # Unhandled exception configuration
        sizer.Add(self._trapcb, 0, wx.ALL|wx.EXPAND, 5)
        # Synchronicity configuration
        sizer.Add(self._synccb, 0, wx.ALL|wx.EXPAND, 5)
        # Auto fork configuration
        sizer.Add(self._forkcb, 0, wx.ALL|wx.EXPAND, 5)
        # Fork mode configuration
        sizer.Add(self._forkchildcb, 0, wx.ALL|wx.EXPAND, 5)
        # Execute/evaluate encoding configuration
        encsz = wx.BoxSizer(wx.HORIZONTAL)
        encsz.Add(self._enclbl, 0, wx.ALIGN_CENTER_VERTICAL)
        encsz.Add((3,3),0)
        encsz.Add(self._encch, 0, wx.EXPAND)
        sizer.Add(encsz, 0, wx.ALL|wx.EXPAND, 5)
        # Execute/evaluate escaping configuration
        sizer.Add(self._esccb, 0, wx.ALL|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def OnTrapExceptionsCheckBox(self, evt):
        config = Profile_Get(PYTOOL_CONFIG, default=dict())
        if evt.GetEventObject() is self._trapcb:
            trap = self._trapcb.GetValue()
            config[TLC_TRAP_EXCEPTIONS] = trap
            RPDBDEBUGGER.set_trap_unhandled_exceptions(trap)
        else:
            evt.Skip()
            return

        Profile_Set(PYTOOL_CONFIG, config)

    def OnSynchronicityCheckBox(self, evt):
        evt_obj = evt.GetEventObject()
        config = Profile_Get(PYTOOL_CONFIG, default=dict())
        if evt_obj is self._synccb:
            synchronicity = self._synccb.GetValue()
            config[TLC_SYNCHRONICITY] = synchronicity
            RPDBDEBUGGER.set_synchronicity(synchronicity)
        else:
            evt.Skip()
            return

        Profile_Set(PYTOOL_CONFIG, config)

    def OnForkCheckBox(self, evt):
        evt_obj = evt.GetEventObject()
        config = Profile_Get(PYTOOL_CONFIG, default=dict())
        if evt_obj in (self._forkcb, self._forkchildcb):
            autofork = not self._forkcb.GetValue()
            config[TLC_AUTO_FORK] = autofork
            forkmode = self._forkchildcb.GetValue()
            config[TLC_FORK_MODE] = forkmode
            RPDBDEBUGGER.set_fork_mode(forkmode, autofork)
        else:
            evt.Skip()
            return

        Profile_Set(PYTOOL_CONFIG, config)

    def OnEncoding(self, evt):
        evt_obj = evt.GetEventObject()
        config = Profile_Get(PYTOOL_CONFIG, default=dict())
        if evt_obj is self._encch:
            encoding = self._encch.GetStringSelection()
            config[TLC_EXECEVALENCODING] = encoding
            escaping = self._esccb.GetValue()
            config[TLC_EXECEVALESCAPING] = escaping
            RPDBDEBUGGER.set_encoding(encoding, escaping)
        else:
            evt.Skip()
            return

        Profile_Set(PYTOOL_CONFIG, config)

    def OnEscapingCheckBox(self, evt):
        evt_obj = evt.GetEventObject()
        config = Profile_Get(PYTOOL_CONFIG, default=dict())
        if evt_obj is self._esccb:
            encoding = self._encch.GetStringSelection()
            config[TLC_EXECEVALENCODING] = encoding
            escaping = self._esccb.GetValue()
            config[TLC_EXECEVALESCAPING] = escaping
            RPDBDEBUGGER.set_encoding(encoding, escaping)
        else:
            evt.Skip()
            return

        Profile_Set(PYTOOL_CONFIG, config)

#-----------------------------------------------------------------------------#

class MessageIDList(eclib.ECheckListCtrl):
    """List to display Pylint message ID's"""
    def __init__(self, *args, **kwargs):
        super(MessageIDList, self).__init__(*args, **kwargs)

        # Attributes
        self._updating = False
        self._config = {}

        # Setup
        self.InsertColumn(0, _("Enabled"))
        self.InsertColumn(1, _("Description"))

    def LoadData(self, data):
        dlist = GetConfigValue(TLC_DISABLED_CHK)
        if dlist is None:
            dlist = list()

        self._updating = True
        keys = data.keys()
        keys.sort()
        for idx, key in enumerate(keys):
            self.Append((key, data[key]))
            self.CheckItem(idx, key not in dlist)
        self._updating = False

    def OnCheckItem(self, index, flag):
        if self._updating:
            return

        item = self.GetItem(index, 0)
        plid = item.GetText()
        dlist = self._config.get(TLC_DISABLED_CHK, list())
        if plid in dlist:
            # Enable it
            dlist.remove(plid)
        else:
            # Disabling it
            dlist.append(plid)
        self._config[TLC_DISABLED_CHK] = dlist
        Profile_Set(PYTOOL_CONFIG, self._config)

    def SetConfig(self, cfg):
        self._config = cfg

#-----------------------------------------------------------------------------#

def _GetPyLintMessageTypes():
    """Get ordered list of display strings for message types
    @return: list of strings

    """
    msgtypes = [_("Convention"),
                _("Refactor"),
                _("Warning"),
                _("Error"),
                _("Fatal")]
    return msgtypes

def Conventions():
    """Get all PyLint convention warnings
    @return: dict warn id => description

    """
    cmsg = {"C0102" : _("Black listed name"),
            "C0103" : _("Invalid name"),
            "C0111" : _("Missing docstring"),
            "C0112" : _("Empty docstring"),
            "C0121" : _("Missing required attribute"),
            "C0202" : _("Class method should have \"cls\" as first argument"),
            "C0203" : _("Metaclass method should have \"mcs\" as first argument"),
            "C0301" : _("Line too long"),
            "C0302" : _("Too many lines in module"),
            "C0321" : _("More than one statement on a single line"),
            "C0322" : _("Operator not preceded by a space"),
            "C0323" : _("Operator not followed by a space"),
            "C0324" : _("Comma not followed by a space")}
    return cmsg

def Refactor():
    rmsg = {"R0001" : _("Messages by category"),
            "R0002" : _("Errors / warnings by module"),
            "R0003" : _("Messages"),
            "R0004" : _("Global evaluation"),
            "R0101" : _("Statistics by type"),
            "R0201" : _("Method could be a function"),
            "R0401" : _("Cyclic import"),
            "R0401" : _("External dependencies"),
            "R0402" : _("Modules dependencies graph"),
            "R0701" : _("Raw metrics"),
            "R0801" : _("Duplication"),
            "R0801" : _("Similar lines in other files"),
            "R0901" : _("Too many ancestors"),
            "R0902" : _("Too many instance attributes"),
            "R0903" : _("Too few public methods"),
            "R0904" : _("Too many public methods"),
            "R0911" : _("Too many return statements"),
            "R0912" : _("Too many branches"),
            "R0913" : _("Too many arguments"),
            "R0914" : _("Too many local variables"),
            "R0915" : _("Too many statements"),
            "R0921" : _("Abstract class not referenced"),
            "R0922" : _("Abstract class is only referenced a few times"),
            "R0923" : _("Interface not implemented")}
    return rmsg

def Warnings():
    wmsg = {"W0101" : _("Unreachable code"),
            "W0102" : _("Dangerous default value used as an argument"),
            "W0104" : _("Statement seems to have no effect"),
            "W0105" : _("String statement has no effect"),
            "W0107" : _("Unnecessary pass statement"),
            "W0108" : _("Lambda may not be necessary"),
            "W0122" : _("Use of the exec statement"),
            "W0141" : _("Used builtin function"),
            "W0142" : _("Used * or ** magic"),
            "W0201" : _("Attribute defined outside __init__"),
            "W0211" : _("Static method with self or class as first argument"),
            "W0212" : _("Access to a protected member of a client class"),
            "W0221" : _("Arguments number differs from super method"),
            "W0222" : _("Signature differs from super method"),
            "W0223" : _("Method of an abstract class is not overridden"),
            "W0231" : _("__init__ method from base class is not called"),
            "W0232" : _("Class has no __init__ method"),
            "W0233" : _("__init__ method from a non direct base class is called"),
            "W0301" : _("Unnecessary semicolon"),
            "W0311" : _("Bad indentation"),
            "W0312" : _("Found inconsistent indentation"),
            "W0331" : _("Use of the <> operator"),
            "W0332" : _("Use l as long integer identifier"),
            "W0333" : _("Use of the `` operator"),
            "W0401" : _("Wildcard import"),
            "W0402" : _("Uses of a deprecated module"),
            "W0403" : _("Relative import"),
            "W0404" : _("Reimport of module"),
            "W0406" : _("Module import itself"),
            "W0410" : _("__future__ import is not the first non docstring statement"),
            "W0511" : _("(warning notes in code comments)"),
            "W0601" : _("Global variable undefined at the module level"),
            "W0602" : _("Global statement used but no assignment is done"),
            "W0603" : _("Using the global statement"),
            "W0604" : _("Using the global statement at the module level"),
            "W0611" : _("Unused import"),
            "W0612" : _("Unused variable"),
            "W0613" : _("Unused argument"),
            "W0614" : _("Unused import from wildcard import"),
            "W0621" : _("Redefining name from outer scope"),
            "W0622" : _("Redefining built-in"),
            "W0631" : _("Using possibly undefined loop variable"),
            "W0701" : _("Raising a string exception"),
            "W0702" : _("No exception type(s) specified"),
            "W0703" : _("Catch \"Exception\""),
            "W0704" : _("Except doesn't do anything"),
            "W0710" : _("Exception doesn't inherit from standard \"Exception\" class"),
            "W1001" : _("Use of \"property\" on an old style class"),
            "W1111" : _("Assigning to function call which only returns None")}
    return wmsg

def Errors():
    emsg = { "E0001" : _("(syntax error raised for a module)"),
             "E0011" : _("Unrecognized file option"),
             "E0012" : _("Bad option value"),
             "E0100" : _("__init__ method is a generator"),
             "E0101" : _("Explicit return in __init__"),
             "E0102" : _("Redefinition of method"),
             "E0103" : _("break or continue used outside a loop"),
             "E0104" : _("Return outside function"),
             "E0105" : _("Yield outside function"),
             "E0106" : _("Return with argument inside generator"),
             "E0202" : _("Method hidden by instance attribute"),
             "E0203" : _("Accessing method before it is defined"),
             "E0211" : _("Method has no argument"),
             "E0213" : _("Method should have \"self\" as first argument"),
             "E0221" : _("Interface is not a class"),
             "E0222" : _("Missing method from interface"),
             "E0501" : _("Non ascii characters found but no encoding specified (PEP 263)"),
             "E0502" : _("Wrong encoding specified"),
             "E0503" : _("Unknown encoding specified"),
             "E0601" : _("Using variable before assignment"),
             "E0602" : _("Undefined variable"),
             "E0611" : _("Name not defined in module"),
             "E0701" : _("Bad except clauses order"),
             "E0702" : _("Raising %s while only classes, instances or string are allowed"),
             "E0710" : _("Raising a new style class which doesn't inherit from BaseException"),
             "E1001" : _("Use __slots__ on an old style class"),
             "E1002" : _("Use super on an old style class"),
             "E1003" : _("Bad first argument given to super class"),
             "E1101" : _("Undefined class member"),
             "E1102" : _("Object is not callable"),
             "E1103" : _("Undefined class member (but some types could not be inferred)"),
             "E1111" : _("Assigning to function call which doesn't return")}
    return emsg

def Fatal():
    fmsg = {"F0001" : _("(error prevented analysis)"),
            "F0002" : _("Unexpected error"),
            "F0003" : _("ignored builtin module"),
            "F0004" : _("unexpected inferred value"),
            "F0202" : _("Unable to check methods signature"),
            "F0220" : _("failed to resolve interfaces"),
            "F0321" : _("Format detection error"),
            "F0401" : _("Unable to import module")}
    return fmsg
