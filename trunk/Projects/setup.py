
from setuptools import setup

__author__ = "Kevin D. Smith"
__doc__ = "Projects"
__version__ = "0.1"

setup(
      name    = "Projects",
      version = __version__,
      description = __doc__,
      author = __author__,
      author_email = "Kevin.Smith@theMorgue.org",
      license = "GPLv2",
      packages = ['projects'],
      entry_points = '''
      [Editra.plugins]
      Projects = projects:Projects
      ''',
     )
