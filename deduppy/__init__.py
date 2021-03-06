#!/usr/bin/env python
# -*- coding: utf-8 vi:noet
# deduppy entry point

__author__ = 'Jérôme Carretero <cJ-deduppy@zougloub.eu>'

from .filestore import *
from .filestore_fs import *
from .filestore_zipfile import *
from .dupfinder import *

try:
    from .filestore_rarfile import *
except ImportError:
    pass

try:
	from .filestore_gdrive import *
except ImportError:
	pass

