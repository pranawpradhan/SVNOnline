# -*- coding: utf-8 -*-
import os, io
from setuptools import setup

from SVNOnline.SVNOnline import __version__
here = os.path.abspath(os.path.dirname(__file__))
README = io.open(os.path.join(here, 'README.rst'), encoding='UTF-8').read()
CHANGES = io.open(os.path.join(here, 'CHANGES.rst'), encoding='UTF-8').read()
setup(name='SVNOnline',
      version=__version__,
      description='A svn online client.',
      long_description=README + '\n\n\n' + CHANGES,
      url='https://github.com/sintrb/SVNOnline',
      classifiers=[
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.7',
          'Topic :: SVN',
      ],
      keywords='SVNOnline Ace.js',
      author='sintrb',
      author_email='sintrb@gmail.com',
      license='Apache',
      packages=['SVNOnline'],
      scripts = ['SVNOnline/SVNOnline', 'SVNOnline/SVNOnline.bat'],
      include_package_data=True,
      zip_safe=False)
