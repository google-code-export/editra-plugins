###############################################################################
# Name: Messages.py                                                           #
# Purpose: PyStudio ed_msg impl                                               #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2011 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
PyStudio Messages

Definitions of ed_msg message types used by PyStudio components.

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#


#-----------------------------------------------------------------------------#

class PyStudioMessages:
    """Namespace for message type identifiers"""
    # msgdata == ContextMenuManager instance
    # Subscribe to this message to add custom options to the PyProject ProjectTree's
    # context menu. MenuManager user data 'path' contains path of file/folder that
    # was clicked on in the ProjectTree.
    PYSTUDIO_PROJECT_MENU = ('PyStudio', 'Project', 'ContextMenu')
