###############################################################################
# Name: CAResultsXml.py                                                       #
# Purpose: XML Persistance class for Code Analysis Results                    #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2011 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
Stores and Loads Code Analysis Results to and from XML

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id:  $"
__revision__ = "$Revision:  $"

#-----------------------------------------------------------------------------#
# Imports
import ed_xml

#-----------------------------------------------------------------------------#

class Result(ed_xml.EdXml):
    """Individual result
    <result line="0" errType="Warning" errMsg="Line too long"/>

    """
    class meta:
        tagname = "result"
    line = ed_xml.String(required=True)
    errType = ed_xml.String(required=True)
    errMsg = ed_xml.String(required=True)

class AnalysisResults(ed_xml.EdXml):
    """Top level XML object
    <pylint path="/path/to/file"></pylint>

    """
    class meta:
        tagname = "pylint"
    path = ed_xml.String(required=True)
    results = ed_xml.List(ed_xml.Model(Result))

    def AddResult(self, line, errType, errMsg):
        result = Result()
        result.line = line
        result.errType = errType
        result.errMsg = errMsg
        self.results.append(result)
