# -*- coding: utf-8 -*-
###############################################################################
# Name: terminal.py                                                           #
# Purpose: Provides a terminal widget that can be embedded in any wxWidgets   #
#          window or run alone as its own shell window.                       #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2007 Cody Precord <staff@editra.org>                         #
# Licence: wxWindows Licence                                                  #
###############################################################################

"""
This script was adapted from the vim plugin 'vimsh' by 
brian m sturk <bsturk@adelphia.net> to the wxWdigets platform utilizing a 
StyledTextCtrl for the interface. It also makes a number of improvements
upon that original script that provide for better output display for long and
continuous running commands due to being able to process in idle time.

It should run on all operating systems that support:
    - wxPython
    - Psuedo TTY's or Pipes/Popen

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports

import sys
import os
import string
import signal
import re
import time
import wx
import wx.stc

# On windows need to use pipes as pty's are not available
try:
    if sys.platform == 'win32':
        import popen2
        import stat
        USE_PTY   = False
    else:
        import pty
        import tty
        import select
        USE_PTY   = True
except ImportError, msg:
    print "[terminal] Error importing required libs: %s" % str(msg)

#-----------------------------------------------------------------------------#
# Globals
DEBUG = True
_ = wx.GetTranslation

if sys.platform == 'win32':
    SHELL = 'cmd.exe'
else:
    if os.environ.has_key('SHELL'):
        SHELL = os.environ['SHELL']
    elif os.environ.has_key('TERM'):
        SHELL = os.environ['TERM']
    else:
        SHELL = '/bin/sh'

# ANSI color code support
ANSI = {
        ## Forground colours ##
        '[30m' : (1, '#000000'),
        '[31m' : (2, '#FF0000'),
        '[32m' : (3, '#00FF00'),
        '[34m' : (4, '#0000FF'),
        '[35m' : (5, '#FF00FF'),
        '[36m' : (6, '#00FFFF'),
        '[37m' : (7, '#FFFFFF'),
        #'[39m' : default

        ## Background colour ##
        '[40m' : (1, '#000000'),
        '[41m' : (2, '#FF0000'),
        '[42m' : (3, '#00FF00'),
        '[44m' : (4, '#0000FF'),
        '[45m' : (5, '#FF00FF'),
        '[46m' : (6, '#00FFFF'),
        '[47m' : (7, '#FFFFFF'),
        #'[49m' : default
        }

RE_COLOUR_START = re.compile('\[[34][0-9]m')
RE_COLOUR_BLOCK = re.compile('\[[34][0-9]m*.*\[m')
RE_COLOUR_END = '[m'
RE_CLEAR_ESC = re.compile('\[[0-9]+m')

# Font settings (TODO make configurable from interface)
FONT = None
FONT_FACE = None
FONT_SIZE = None
#-----------------------------------------------------------------------------#
class Xterm(wx.stc.StyledTextCtrl):
    """Creates a graphical terminal that works like the system shell
    that it is running on (bash, command, ect...).

    """
    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition, 
                 size=wx.DefaultSize, style=0):
        wx.stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)

        # Attributes
        ##  The lower this number is the more responsive some commands
        ##  may be ( printing prompt, ls ), but also the quicker others
        ##  may timeout reading their output ( ping, ftp )
        self.delay = 0.02
        self._fpos = 0          # First allowed cursor position
        self._exited = False    # Is shell still running
        self.last_cmd_executed = ''
        self._setspecs = list()

        # Setup
        self.__Configure()
        self.__ConfigureStyles()
        self.__ConfigureKeyCmds()
        self._SetupPTY()

        #---- Event Handlers ----#
        # General Events
        self.Bind(wx.EVT_IDLE, self.OnIdle)

        # Key events
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_CHAR, self.OnChar)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

        # Menu Events
        self.Bind(wx.EVT_MENU, lambda evt: self.Cut(), id=wx.ID_CUT)
        self.Bind(wx.EVT_MENU, lambda evt: self.Copy(), id=wx.ID_COPY)
        self.Bind(wx.EVT_MENU, lambda evt: self.Paste(), id=wx.ID_PASTE)
        self.Bind(wx.EVT_MENU, lambda evt: self.SelectAll(), id=wx.ID_SELECTALL)

        # Mouse Events
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
#         self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateUI)

    def __del__(self):
        DebugLog("[terminal][info] Terminal instance is being deleted")
        self._CleanUp()

    def __ConfigureKeyCmds(self):
        """Clear the builtin keybindings that we dont want"""
        self.CmdKeyClear(ord('U'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('Z'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(wx.WXK_BACK, wx.stc.STC_SCMOD_CTRL | wx.stc.STC_SCMOD_SHIFT)
        self.CmdKeyClear(wx.WXK_DELETE, wx.stc.STC_SCMOD_CTRL | wx.stc.STC_SCMOD_SHIFT)
        self.CmdKeyClear(ord('['), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord(']'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('\\'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('/'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('L'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('D'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('Y'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('T'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(wx.WXK_TAB, wx.stc.STC_SCMOD_NORM)

    def __Configure(self):
        """Configure the base settings of the control"""
        self.SetEOLMode(wx.stc.STC_EOL_LF)
        self.SetViewWhiteSpace(False)
        self.SetTabWidth(0)
        self.SetUseTabs(False)
        self.SetWrapMode(True)
        self.SetEndAtLastLine(False)
        self.SetVisiblePolicy(1, wx.stc.STC_VISIBLE_STRICT)

    def __ConfigureStyles(self):
        """Configure the text coloring of the terminal"""
        # Clear Styles
        self.StyleResetDefault()
        self.StyleClearAll()

        # Set margins
        self.SetMargins(4, 4)
        self.SetMarginWidth(wx.stc.STC_MARGIN_NUMBER, 0)

        # Caret styles
        self.SetCaretWidth(4)
        self.SetCaretForeground(wx.NamedColor("white"))

        # Configure text styles
        # TODO make this configurable
        fore = "#FEFEFE"
        back = "#000000"
        global FONT
        global FONT_SIZE
        global FONT_FACE
        FONT = wx.Font(11, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, 
                               wx.FONTWEIGHT_NORMAL)
        FONT_FACE = FONT.GetFaceName()
        FONT_SIZE = FONT.GetPointSize()
        self.StyleSetSpec(0, "face:%s,size:%d,fore:%s,back:%s,bold" % (FONT_FACE, FONT_SIZE, fore, back))
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, \
                          "face:%s,size:%d,fore:%s,back:%s,bold" % (FONT_FACE, FONT_SIZE, fore, back))
        self.StyleSetSpec(wx.stc.STC_STYLE_CONTROLCHAR, \
                          "face:%s,size:%d,fore:%s,back:%s" % (FONT_FACE, FONT_SIZE, fore, back))
        self.Colourise(0, -1)

    #---- Protected Members ----#
    def _ApplyStyles(self, data):
        """Apply style bytes to regions of text that require them, starting
        at self._fpos and using the postional data as on offset from that point.

        @param data: list of tuples [ (style_start, colour, style_end) ]

        """
        for pos in data:
            spec = ANSI[pos[1]][0]
            if spec not in self._setspecs:
                DebugLog("[terminal][styles] Setting Spec: %d" % spec)
                self._setspecs.append(spec)
                self.StyleSetSpec(spec, "fore:%s,back:#000000,face:%s,size:%d" % (ANSI[pos[1]][1], FONT_FACE, FONT_SIZE))
            self.StartStyling(self._fpos + pos[0], 0xff)
            self.SetStyling(pos[2] - pos[0] + 1, spec)

    def _CheckAfterExe(self):
        """Check std out for anything left after an execution"""
        DebugLog("[terminal][info] Checking after cmd execution")
        self.Read()
        self.CheckForPassword()

    def _CleanUp(self):
        """Cleanup open file descriptors"""
        if self._exited:
            DebugLog("[terminal][exit] Already exited")
            return

        try:
            DebugLog("[terminal][exit] Closing FD and killing process")
            if not USE_PTY:
                os.close(self.ind)
                os.close(self.outd)

            os.close(self.errd)       ##  all the same if pty
            if USE_PTY:
                os.kill(self.pid, signal.SIGKILL)
                time.sleep(self.delay) # give some time for the process to die

        except Exception, msg:
            DebugLog("[terminal][err] %s" % str(msg))

        DebugLog("[terminal][cleanup] Finished Cleanup")

    def _EndRead(self, any_lines_read):
        """Finish up after reading"""
        # Mark earliest valid cursor position in buffer
        self._fpos = self.GetCurrentPos()
        if (not USE_PTY and any_lines_read):
            self.LineDelete()
            DebugLog("[terminal][endread] Deleted trailing line")
            self._fpos = self.GetCurrentPos()

        DebugLog("[terminal][info] Set valid cursor to > %d" % self._fpos)
#         self.ScrollToLine(self.GetCurrentLine())
        self.EnsureCaretVisible()

    def _HandleExit(self, cmd):
        """Handle closing the shell connection"""
        ##  Exit was typed, could be the spawned shell, or a subprocess like
        ##  telnet/ssh/etc.
        DebugLog("[terminal][exit] Exiting process")
        if not self._exited:
            try:
                DebugLog("[terminal][exit] Shell still around so trying to close")
                self.Write(cmd + '\n')
                self._CheckAfterExe()
            except Exception, msg:            
                DebugLog("[terminal][err] Exception on exit: %s" % str(msg))

                ## shell exited, self._exited may not have been set yet in
                ## sigchld_handler.
                DebugLog("[terminal][exit] Shell Exited is: " + str(self._exited))
                self.ExitShell()

    def _ProcessRead(self, lines):
        """Process the raw lines from stdout"""
        DebugLog("[terminal][info] Processing Read...")
        lines_to_print = lines.split('\n')

        #  Filter out invalid blank lines from begining/end input
        if sys.platform == 'win32':
            m = re.search(re.escape(self.last_cmd_executed.strip()), lines_to_print[0])
            if m != None or lines_to_print[0] == "":
                DebugLog('[terminal][info] Win32, removing leading blank line')
                lines_to_print = lines_to_print[ 1: ]

        num_lines = len(lines_to_print)
        if num_lines > 1:
            last_line = lines_to_print[num_lines - 1].strip()

            if last_line == "":
                lines_to_print = lines_to_print[ :-1 ]

        errors = self.CheckStdErr()
        if errors:
            DebugLog("[terminal][err] Process Read Prepending stderr --> ", errors)
            lines_to_print = errors + lines_to_print

        return lines_to_print

    def _SetupPTY(self):
        """Setup the connection to the real terminal"""
        if USE_PTY:
            self.master, pty_name = pty.openpty()
            DebugLog("[terminal][info] Slave Pty name: " + str(pty_name))

            self.pid, self.fd = pty.fork()

            self.outd = self.fd
            self.ind  = self.fd
            self.errd = self.fd

            signal.signal(signal.SIGCHLD, self._SigChildHandler)

            if self.pid == 0:
                attrs = tty.tcgetattr( 1 )

                attrs[ 6 ][ tty.VMIN ]  = 1
                attrs[ 6 ][ tty.VTIME ] = 0
                attrs[ 0 ] = attrs[ 0 ] | tty.BRKINT
                attrs[ 0 ] = attrs[ 0 ] & tty.IGNBRK
                attrs[ 3 ] = attrs[ 3 ] & ~tty.ICANON & ~tty.ECHO

                tty.tcsetattr(1, tty.TCSANOW, attrs)
                os.execv(SHELL, [ SHELL, ])

            else:
                try:
                    attrs = tty.tcgetattr(1)
                    termios_keys = attrs[6]
                except:
                    DebugLog('[terminal][err] tcgetattr failed')
                    return

                #  Get *real* key-sequence for standard input keys, i.e. EOF
                self.eof_key   = termios_keys[ tty.VEOF ]
                self.eol_key   = termios_keys[ tty.VEOL ]
                self.erase_key = termios_keys[ tty.VERASE ]
                self.intr_key  = termios_keys[ tty.VINTR ]
                self.kill_key  = termios_keys[ tty.VKILL ]
                self.susp_key  = termios_keys[ tty.VSUSP ]
        else:
            ##  Use pipes on Win32. not as reliable/nice. works OK but with limitations.
            self.delay = 0.1

            try:
                import win32pipe
                DebugLog('[terminal][info] using windows extensions')
                self.stdin, self.stdout, self.stderr = win32pipe.popen3(SHELL)
            except ImportError:
                DebugLog('[terminal][info] not using windows extensions')
                self.stdout, self.stdin, self.stderr = popen2.popen3(SHELL, -1, 'b')

            self.outd = self.stdout.fileno()
            self.ind  = self.stdin.fileno()
            self.errd = self.stderr.fileno()

            self.intr_key = ''
            self.eof_key  = ''

    def _SigChildHandler(self, sig, frame):
        """Child process signal handler"""
        DebugLog("[terminal][info] caught SIGCHLD")
        self._WaitPid()

    def _WaitPid(self):
        """Mark the original shell process as having gone away if it
        has exited.

        """
        if os.waitpid(self.pid, os.WNOHANG)[0]:
            self._exited = True
            DebugLog("[terminal][waitpid] Shell process has exited")
        else:
            DebugLog("[terminal][waitpid] Shell process hasn't exited")

    #---- End Protected Members ----#

    #---- Public Members ----#
    def CanCopy(self):
        """Check if copy is possible"""
        return self.GetSelectionStart() != self.GetSelectionEnd()

    def CanCut(self):
        """Check if selection is valid to allow for cutting"""
        s_start = self.GetSelectionStart()
        s_end = self.GetSelectionEnd()
        return s_start != s_end and s_start >= self._fpos and s_end >= self._fpos

    def CheckForPassword(self):
        """Check if the shell is waiting for a password or not"""
        prev_line = self.GetLine(self.GetCurrentLine() - 1)
        for regex in ['^\s*Password:', 'password:', 'Password required']:
            if re.search(regex, prev_line):
                try:
                    print "FIX ME"
                except KeyboardInterrupt:
                    return

                # send the password to the 
#                 self.ExecuteCmd([password])

    def CheckStdErr(self):
        """Check for errors in the shell"""
        errors  = ''
        if sys.platform == 'win32':
            err_txt  = self.PipeRead(self.errd, 0)
            errors   = err_txt.split('\n')

            num_lines = len(errors)
            last_line = errors[num_lines - 1].strip()

            if last_line == "":
                errors = errors[ :-1 ]

        return errors

    def ClearScreen(self):
        """Clear the screen so that all commands are scrolled out of
        view and a new prompt is shown on the top of the screen.

        """
        self.AppendText("\n" * 5)
        self.Write("\n")
        self._CheckAfterExe()
        self.Freeze()
        wx.PostEvent(self, wx.ScrollEvent(wx.wxEVT_SCROLLWIN_PAGEDOWN, 
                                          self.GetId(), orient=wx.VERTICAL))
        wx.CallAfter(self.Thaw)

    def ExecuteCmd(self, cmd=None, null=1):
        """Run the command entered in the buffer"""
        DebugLog("terminal][exec] Running command: %s" % str(cmd))

        try:
            # Get text from prompt to eol when no command is given
            if cmd is None:
                cmd = self.GetTextRange(self._fpos, self.GetLength())

            # Move output position past input command
            self._fpos = self.GetLength()

            # Process command
            if len(cmd) and cmd[-1] != '\t':
                cmd = cmd.strip()

            if re.search( r'^\s*\bclear\b', cmd) or re.search( r'^\s*\bcls\b', cmd):
                DebugLog('[terminal][exec] Clear Screen')
                self.ClearScreen()

            elif re.search( r'^\s*\exit\b', cmd):
                DebugLog('[terminal][exec] Exit terminal session')
                self._HandleExit(cmd)
                self.SetCaretForeground(wx.BLACK)

            else:
                if null:
                    self.Write(cmd + os.linesep)
                else:
                    self.Write(cmd)

                self.last_cmd_executed = cmd
                self._CheckAfterExe()

            self.last_cmd_executed = cmd

        except KeyboardInterrupt:
            pass

    def ExitShell(self):
        """Cause the shell to exit"""
        if not self._exited:
            self._CleanUp()

        self.PrintLines(["[process complete]\n"])
        self.SetReadOnly(True)

    def GetContextMenu(self):
        """Create and return a context menu to override the builtin scintilla
        one. To prevent it from allowing modifications to text that is to the
        left of the prompt.

        """
        menu = wx.Menu()
        menu.Append(wx.ID_CUT, _("Cut"))
        menu.Append(wx.ID_COPY, _("Copy"))
        menu.Append(wx.ID_PASTE, _("Paste"))
        menu.AppendSeparator()
        menu.Append(wx.ID_SELECTALL, _("Select All"))
        menu.AppendSeparator()
        menu.Append(wx.ID_SETUP, _("Preferences"))

        return menu

    def NewPrompt(self):
        """Put a new prompt on the screen and make all text from end of
        prompt to left read only.

        """
        self.ExecuteCmd("")

    def OnContextMenu(self, evt):
        """Display the context menu"""
        self.PopupMenu(self.GetContextMenu())

    def OnIdle(self, evt):
        """While idle check for more output"""
        if not self._exited:
            self.Read()

    def OnKeyDown(self, evt):
        """Handle key down events"""
        if self._exited:
            return

        key = evt.GetKeyCode()
        if key == wx.WXK_RETURN:
            self.CmdKeyExecute(wx.stc.STC_CMD_NEWLINE)
            self.ExecuteCmd()
        elif key == wx.WXK_TAB:
            # TODO Tab Completion
#             self.ExecuteCmd(self.GetTextRange(self._fpos, self.GetCurrentPos()) + '\t', 0)
            pass
        elif key in [wx.WXK_UP, wx.WXK_NUMPAD_UP]:
            # Cycle through command history
            pass
        elif key in [wx.WXK_LEFT, wx.WXK_NUMPAD_LEFT, 
                     wx.WXK_BACK, wx.WXK_DELETE]:
            if self.GetCurrentPos() > self._fpos:
                evt.Skip()
        elif key == wx.WXK_HOME:
            # Go Prompt Start
            self.GotoPos(self._fpos)
        else:
            evt.Skip()

    def OnChar(self, evt):
        """Handle character enter events"""
        # Dont allow editing of earlier portion of buffer
        if self.GetCurrentPos() < self._fpos:
            return
        evt.Skip()

    def OnKeyUp(self, evt):
        """Handle when the key comes up"""
        evt.Skip()

    def OnLeftDown(self, evt):
        """Set selection anchor"""
        pos = evt.GetPosition()
        self.SetSelectionStart(self.PositionFromPoint(pos))

    def OnLeftUp(self, evt):
        """Check click position to ensure caret doesn't 
        move to invalid position.

        """
        evt.Skip()
        pos = evt.GetPosition()
#         self.SetSelectionEnd(self.PositionFromPoint(pos))
        if self._fpos > self.PositionFromPoint(pos):
            wx.CallAfter(self.GotoPos, self._fpos)

    def OnUpdateUI(self, evt):
        """Enable or disable menu events"""
        e_id = evt.GetId()
        if e_id == wx.ID_CUT:
            evt.Enable(self.CanCut())
        elif e_id == wx.ID_COPY:
            evt.Enable(self.CanCopy())
        elif e_id == wx.ID_PASTE:
            evt.Enable(self.CanPaste())
        else:
            evt.Skip()

    def PrintLines(self, lines):
        """Print lines to the terminal buffer
        @param lines: list of strings

        """
        if len(lines) and lines[0].strip() == self.last_cmd_executed.strip():
            lines.pop(0)

        num_lines = len(lines)
        for line in lines:
            DebugLog("[terminal][print] Current line is --> %s" % line)
            m = None
            while re.search( '\r$', line):
                DebugLog('[terminal][print] removing trailing ^M' )
                line = line[:-1]
                m = True

            # Put the line
            need_style = False
            if r'' in line:
                DebugLog('[terminal][print] found ansi escape sequence(s)')
                c_items = re.findall(RE_COLOUR_BLOCK, line)
                colors = re.findall(RE_COLOUR_START, line)

                # construct a list of [ (style_start, colour, style_end) ]
                # where the start end positions are offsets of the curent _fpos
                tmp = line
                positions = list()
                i = 0
                for pat in c_items:
                    ind = tmp.find(pat)
                    color = re.findall(RE_COLOUR_START, pat)[0]
                    tpat = pat.replace(color, '').replace(RE_COLOUR_END, '')
                    tmp = tmp.replace(pat, tpat, 1)
                    positions.append((ind, color, ind + len(tpat)))
                    i = i + 1

                # Try to remove any trailing escape sequences that may still be present.
                line = tmp.replace(RE_COLOUR_END, '')
                line = re.sub(RE_COLOUR_START, '', line)
                line = re.sub(RE_CLEAR_ESC, '', line)
                
                need_style = True

            self.AppendText(line)

            # Apply any colouring that was found
            if need_style:
                DebugLog('[terminal][print] applying styles to output string')
                self._ApplyStyles(positions)

            # Move cursor to end of buffer
            self._fpos = self.GetLength()
            self.GotoPos(self._fpos)

            ##  If there's a '\n' or using pipes and it's not the last line
            if not USE_PTY or m:
                DebugLog("[terminal][print] Appending new line since ^M or not using pty")
                self.AppendText("\n")

    def PipeRead(self, pipe, minimum_to_read):
        """Read from pipe, used on Windows. This is needed because select
        can only be used with sockets on Windows and not with any other type
        of file descriptor.

        """
        DebugLog("[terminal][pipe] minimum to read is " + str(minimum_to_read))

        time.sleep(self.delay)
        count = os.fstat(pipe)[stat.ST_SIZE]
        data = ''
        DebugLog("[terminal][pipe] initial count via fstat is " + str(count))

        while (count > 0):
            tmp = os.read(pipe, 1)
            data += tmp

            count = os.fstat(pipe)[stat.ST_SIZE]
            if len(tmp) == 0:
                DebugLog("[terminal][pipe] count %s but nothing read" % str(count))
                break

            #  Be sure to break the read, if asked to do so,
            #  after we've read in a line termination.
            if minimum_to_read != 0 and len(data) > 0 and data[len(data) - 1] == '\n':
                if len(data) >= minimum_to_read:
                    DebugLog("[terminal][pipe] read minimum and found termination")
                    break
                else:
                    dbg_print("[terminal][pipe] more data to read: count is " + str(count))

        return data

    def Read(self):
        """Read output from stdin"""
        num_iterations = 0  #  counter for periodic redraw
        any_lines_read = 0  #  sentinel for reading anything at all

        lines = ''
        while 1:
            if USE_PTY:
                r, w, e = select.select([self.outd], [], [], self.delay)
            else:
                r = [1,]  # pipes, unused

            for file_iter in r:
                if USE_PTY:
                    tmp = os.read(self.outd, 32)
                else:
                    tmp = self.PipeRead(self.outd, 2048)

                lines += tmp
                if tmp == '':
                    DebugLog('[terminal][read] No more data on stdout Read')
                    r = []
                    break

                any_lines_read  = 1 
                num_iterations += 1

            if not len(r) and len(lines):
                DebugLog('[terminal][read] End of Read, starting processing and printing' )
                lines = self._ProcessRead(lines)
                self.PrintLines(lines)
                self._EndRead(any_lines_read)
                break
            elif not any_lines_read and not num_iterations:
                break
            else:
                pass

    def Write(self, cmd):
        """Write out command to shell process"""
        DebugLog("[terminal][info] Writting out command: " + cmd)
        os.write(self.ind, cmd)

#-----------------------------------------------------------------------------#
# Utility Functions
def DebugLog(msg):
    """Print debug messages"""
    if DEBUG:
        print msg

#-----------------------------------------------------------------------------#
# For Testing

if __name__ == '__main__':
    app = wx.PySimpleApp(False)
    frame = wx.Frame(None, wx.ID_ANY, "Terminal Test")
    term = Xterm(frame, wx.ID_ANY)
    
    fsizer = wx.BoxSizer(wx.VERTICAL)
    fsizer.Add(term, 1, wx.EXPAND)
    frame.SetSizer(fsizer)
    
    frame.SetSize((600, 400))
    frame.Show()
    app.MainLoop()
