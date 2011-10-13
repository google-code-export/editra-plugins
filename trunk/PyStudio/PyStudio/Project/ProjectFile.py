###############################################################################
# Name: ProjectFile.py                                                        #
# Purpose: Project File Abstraction                                           #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2011 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
ProjectFile

Project Data class representing the Project file

@see: ProjectXml

"""

#-----------------------------------------------------------------------------#
# Imports
import os

#-----------------------------------------------------------------------------#

class ProjectFile(object):
    """Project file for use by the ProjectMgr"""
    def __init__(self, pxml, path):
        """
        @param pxml: ProjectXml
        @param path: Xml file path

        """
        super(ProjectFile, self).__init__()

        # Attributes
        self._pxml = pxml
        self._path = path

    #---- Properties ----#
    Path = property(lambda self: self._path)
    ProjectRoot = property(lambda self: os.path.dirname(self.Path))

    #---- Implementation ---- #
    def Save(self):
        """Save the project file to disk"""
        self._pxml.Write(self.Path)
