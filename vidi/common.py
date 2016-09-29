import ctypes
from enum import Enum
from PIL import Image as PILImage


__all__ = [
    # Classes
    'DebugSink', 'GPUMode', 'Buffer',
]

class DebugSink(Enum):
    """ Debug sink mode
    """
    console = 0
    file = 1
    stop = 2

class GPUMode(Enum):
    """ GPU mode
    """
    cpu = -1
    single = 0
    multiple = 1

#class ToolType(Enum):
#    red   = "red"
#    green = "green"
#    blue  = "blue"


class __Buffer__(ctypes.Structure):
    """ C Buffer wrapper
    """
    _fields_ = [("size", ctypes.c_int), ("data", ctypes.c_char_p)]


class Buffer():
    """ vidi managed buffer
    """
    def __init__(self, cdll=None):
        self.owner = cdll
        self.pointer = None

    def __enter__(self):
        if self.owner is not None:
            self.pointer = self.owner.init_buffer()
        return self

    def __exit__(self, type, value, traceback):
        if self.owner is not None:
            self.owner.free_buffer(self.pointer)


class Image(ctypes.Structure):
    """ C Image wrapper using PIL
    """
    _fields_ = [("width", ctypes.c_uint),
                ("height", ctypes.c_uint),
                ("channels", ctypes.c_uint),
                ("data", ctypes.POINTER(ctypes.c_char)),
                ("channel_depth", ctypes.c_uint),
                ("step", ctypes.c_uint)]

    def __init__(self):
        self.width = 0
        self.height = 0
        self.step = 0
        self.channels = 0
        self.channel_depth = 0
     #   self.data = c.Pointer(c.c_char)

    def load_image(self, image_path):
        my_image = PILImage.open(image_path)
        self.width = my_image.size[0]
        self.height = my_image.size[1]
        self.step = 0

        if my_image.mode == "L":
            self.channels = 1
            self.channel_depth = 0
        elif my_image.mode == "RGB":
            #  make it BGR
            b, g, r = my_image.split()
            my_image = PILImage.merge("RGB", (r, g, b))
            self.channels = 3
            self.channel_depth = 0
        elif my_image.mode == "BGR":
            self.channels = 3
            self.channel_depth = 0
        else:
            raise RuntimeError("unsupported image type")

        _bytes = my_image.tobytes("raw")
        self.data = ctypes.create_string_buffer(_bytes)

def _vidi_str(input_str):
    """ vidi uses this method internally to wrap to a C string
    """
    c_input_str = ctypes.c_char_p()
    c_input_str.value = input_str.encode("utf-8")
    return c_input_str

