

"""
ViDi Python wrapper
~~~~~~~~~~~~~~~~~~~~~

"""

__title__ = 'vidi'
__version__ = '2.0.0'
__author__ = 'ViDI Systems'
__license__ = 'ViDi License'
__copyright__ = 'Copyright 2016 ViDi Systems SA'

from .common import Image, Buffer, DebugSink, GPUMode
from .VidiRuntime import Control as Runtime
from .VidiRuntime import Sample

