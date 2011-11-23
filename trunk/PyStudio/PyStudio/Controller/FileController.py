###############################################################################
# Name: FileController.py                                                     #
# Purpose: Project File Manager                                               #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2011 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
File Controller Base Class

Defines base interface for file controllers used by the ProjectTree user
interface.

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Dependencies
import os
import sys

# Editra Imports
import ebmlib

#-----------------------------------------------------------------------------#

class FileController(ebmlib.FactoryMixin):
    """Base factory for file controllers which implements all interface
    methods using default filesystem actions.

    """
    def __init__(self):
        super(FileController, self).__init__()

        # Attributes
        
    @classmethod
    def GetMetaDefaults(cls):
        """Return mapping of default meta-data
        base class implements the controller for the operating systems file
        system. Subclasses should define their own nested `meta` class that
        defines the `system` attribute which is used to identify the appropriate
        controller to use.

        """
        return dict(system="OS")

    #---- Interface Implementation ----#

    def CreateFile(self, path, name):
        """Create a new file at the given path
        @param path: directory path
        @param name: file name

        """
        ebmlib.MakeNewFile(path, name)

    def CreateFolder(self, path, name):
        """Create a new folder at the given path
        @param path: directory path
        @param name: folder name

        """
        ebmlib.MakeNewFolder(path, name)

    def MoveToTrash(self, path):
        """Move the given path to the trash
        @param path: file/folder path

        """
        ebmlib.MoveToTrash(path)

    def Rename(self, old, new):
        """Rename a file or folder
        @param old: current file path
        @param new: new name (path) for old
        @return: bool (success / fail)

        """
        try:
            os.rename(old, new)
        except OSError:
            return False
        return True
