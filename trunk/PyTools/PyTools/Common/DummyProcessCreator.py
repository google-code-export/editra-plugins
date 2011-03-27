# -*- coding: utf-8 -*-
# Name: DummyProcessCreator.py
# Purpose: Create asynchronous processes
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" Utility functions """

__author__ = "Mike Rans"
__svnid__ = "$Id: DummyProcessCreator.py 1174 2011-03-26 13:23:04Z rans@email.com $"
__revision__ = "$Revision: 1174 $"

class DummyProcessCreator(object):
    def __init__(self, pid, textfn):
        super(DummyProcessCreator, self).__init__()
        self.pid = pid
        self.AddText = textfn

    def GetPID(self):
        return self.pid
