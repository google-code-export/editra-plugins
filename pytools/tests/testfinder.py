###############################################################################
# Name: testfinder.py
# Purpose: Unittest for pytools.finder
# Author: Rudi Pettazzi <rudi.pettazzi@gmail.com>
# Copyright: (c) 2009 Cody Precord <staff@editra.org>
# License: wxWindows License
###############################################################################

__author__ = "Rudi Pettazzi <rudi.pettazzi@gmail.com>"
__svnid__ = "$Id: Exp $"
__revision__ = "$Revision:  $"

#-----------------------------------------------------------------------------#
# Imports
import unittest
import StringIO
import os
import sys

sys.path.insert(0, os.path.abspath('../pytools'))

import finder

#-----------------------------------------------------------------------------#

# TODO initial stub of unit tests for ModuleFinder
class TestModuleFinder(unittest.TestCase):
    def setUp(self):
        self.finder = finder.ModuleFinder(finder.getSearchPath())

    def tearDown(self):
        pass

    def testFindUseImport(self):
        res = self.finder.Find('string', True)
        self.assertEquals(res[0], os.path.join(sys.prefix, 'lib', 'string.py'))

    def testFind(self):
        list = []
        res = self.finder.Find('string')
        self.assertTrue(res.index(os.path.join(sys.prefix, 'Lib', 'string.py')) > -1)

        # FIXME quick hack for windows: you get
        # C:\Python25\lib in sys.path and C:\Python25\Lib from os.path when traversing
        # res = dict([ (x.lower(), x) for x in result if x != '' ])

if __name__ == '__main__':
    unittest.main()



