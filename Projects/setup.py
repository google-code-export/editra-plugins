
from setuptools import setup

__author__ = "Kevin D. Smith <Kevin.Smith@sixquickrun.com>"
__revision__ = "$Revision$"
__scid__ = "$Id$"
__doc__ = "Projects"
__version__ = "0.2"

setup(
      name    = "Projects",
      version = __version__,
      description = __doc__,
      author = "Kevin D. Smith",
      author_email = "Kevin.Smith@theMorgue.org",
      license = "wxWindows",
      packages = ['projects'],
      entry_points = '''
      [Editra.plugins]
      Projects = projects:Projects
      ''',
     )
