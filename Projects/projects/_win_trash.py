###############################################################################
# Name: win32shell.py                                                         #
# Purpose: ctypes wrapper for moving files to recycle bin                     #
# Author: Rudi Pettazzi <rudi.pettazzi@gmail.com>                             #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
FILE: win32shell.py
AUTHOR: Rudi Pettazzi
@summary: ctypes wrapper for moving files to recycle bin

"""

__author__ = ""
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
from ctypes import *
import sys

#-----------------------------------------------------------------------------#
# Globals

# from shellapi.h
FO_DELETE = 0x003
FOF_NOCONFIRMATION = 0x0010
FOF_SILENT = 0x0004
FOF_ALLOWUNDO = 0x0040
FOF_NOCONFIRMMKDIR = 0x0200
FOF_NOERRORUI = 0x0400
FOF_NO_UI = (FOF_SILENT | FOF_NOCONFIRMATION | FOF_NOERRORUI | FOF_NOCONFIRMMKDIR)
MAX_PATH = 260

#-----------------------------------------------------------------------------#

# see http://msdn.microsoft.com/en-us/library/bb759795(VS.85).aspx
# XXX check if ctypes contains c defines (e.g. DWORD) for the win32 types.
class SHFILEOPSTRUCT(Structure):
    _fields_ = [("hwnd", c_int),
                ("wFunc", c_int),
                ("pFrom", c_wchar_p),
                ("pTo", c_wchar_p),
                ("fFlags", c_int),
                ("fAnyOperationsAborted", c_int),
                ("hNameMappings", c_int),
                ("lpszProgressTitle", c_wchar_p) ]

def Win32Delete(abspath, errorui=False):
    """Move the file identified by the given path to the recyle bin
    using SHFileOperationW.
    @param abspath: absolute file or directory path
    @param errorui: if True show message box on error. Default to False
    @return: -1 if the file name is longer than MAX_PATH-1,
    SHFileOperationW return value otherwise (0 if successful)

    """
    # filename must be less than MAX_PATH because MAX_PATH includes the '\0'
    # terminator
    if len(abspath) >= MAX_PATH:
        return -1

    flags = FOF_NOCONFIRMATION | FOF_ALLOWUNDO
    if not errorui:
        flags |= FOF_NOERRORUI | FOF_SILENT

    op = SHFILEOPSTRUCT()
    op.wFunc = FO_DELETE
    op.fFlags = flags
    op.pFrom = abspath + u'\0'
    op.hwnd = 0
    op.pTo = None
    op.fAnyOperationsAborted = 0
    op.hNameMappings = 0
    op.lpszProgressTitle = None
    result = windll.shell32.SHFileOperationW(byref(op))
    return result

#-----------------------------------------------------------------------------#

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        result = Win32Delete(filename, False)
        print result
    else:
        print 'filename required'
