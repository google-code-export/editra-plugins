###############################################################################
# Name: __init__.py                                                           #
# Purpose: PyDebugger plugin for integrating a Python debugger in Editra      #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

""" PyDebugger
Plugin to integrate a debugger for python.

@summary: Integrates a Python debugging in Editra

"""
__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#

# Editra Libraries
import plugin

#-----------------------------------------------------------------------------#

class PyDebugger(plugin.Plugin):
    """Python Debugger Plugin"""
    
