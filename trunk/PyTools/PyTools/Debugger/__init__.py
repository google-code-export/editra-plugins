# -*- coding: utf-8 -*-
# Name: __init__.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra global variables"""

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#----------------------------------------------------------------------------#
# Local Imports
from PyTools.Debugger.MessageHandler import MessageHandler
from PyTools.Debugger.RpdbDebugger import RpdbDebugger

# Globals
RPDBDEBUGGER = RpdbDebugger()
MESSAGEHANDLER = MessageHandler(RPDBDEBUGGER)
#----------------------------------------------------------------------------#
