from .common import _vidi_str
from .common import GPUMode
from .common import DebugSink
from .common import Image
from .common import Buffer
from .common import __Buffer__

import ctypes
import xml.etree.ElementTree as ET
import platform
has_numpy = True
try :
    import numpy as np
except ImportError:
    has_numpy = False

__all__ = [
    # Classes
    'Sample', 'Control'
]

class Sample :
    """ parses the XML response from process and provides results as a marking dictionary
    """
    markings = {}
    def __init__(self,input_str):
        """
        :rtype: Sample
        """
        self.xmlFramgment = input_str
        self.xmlDoc = ET.fromstring(self.xmlFramgment)

        marking_nodes = self.xmlDoc.findall("image/marking")

        for marking_node in marking_nodes :
            m = marking_node.attrib
            views = marking_node.findall('view')
            views_list = []
            for view in views:
                view_entry = \
                {
                    'size' : [float(x) for x in view.attrib['size'].split('x')]
                }
                if has_numpy :
                    view_entry['pose'] = np.matrix(view.attrib['pose']).reshape(3,2).transpose()
                else:
                    view_entry['pose'] =[float(x) for x in view.attrib['pose'].split(',')]

                for redview in view.findall('red'):
                    view_entry['score'] = float(redview.attrib['score'])
                    view_entry['mode'] = redview.attrib['mode']
                    view_entry['treshold'] =[float(x) for x in redview.attrib['threshold'].strip('[]').split(',')]

                    view_entry.update( { resource.attrib['name'] :  {'uuid' : resource.attrib['uuid']} for resource in redview.findall('resource') })
                    regions = []
                    for region in redview.findall('region'):
                        region_dict = {}
                        region_dict['area'] = float(region.attrib['area'])
                        region_dict['center'] = [float(x) for  x in  region.attrib['center'].split(',')]
                        region_dict['score'] = float(region.attrib['score'])
                        region_dict['points'] = region.attrib['points']
                        regions.append(region_dict)

                    view_entry.update({"regions": regions})

                for greenview in view.findall('green'):
                     view_entry.update({'tag' :{ {r.attrib['name'] : float(r.attrib['score']) }for r in redview.findall('tag') }})

                for blueview in view.findall('blue'):
                     view_entry.update({'features' : [
                                                     {
                                                         'id'     : r.attrib['id'],
                                                         'score' : float(r.attrib['score']),
                                                         'loc' :  [float(x) for x  in  r.attrib['loc'].split(',')] ,
                                                         'size' :  float(r.attrib['size']) ,
                                                         'angle' :  float(r.attrib['angle'])
                                                     }for r in blueview.findall('feat') ]})
                     matches = []
                     for match in blueview.findall('match'):
                        match_dict = {}
                        match_dict['model_id'] = match.attrib['model_id']
                        match_dict['score'] = float(match.attrib['score'])
                        match_dict['node_coords'] = match.attrib['node_coords']
                        match_dict['string'] = match.attrib['string']
                        match_dict['model_id'] = match.attrib['model_id']
                        pose_node = match.find('pose')
                        match_dict['pose'] = np.matrix(pose_node.attrib['matrix']).reshape(3,2).transpose()
                        match_dict['feat'] =[x.attrib['idx'] for x in match.findall('feat')]
                        matches.append(match_dict)
                     view_entry['matches'] = matches

                views_list.append(view_entry)
                m['views'] = views_list
            self.markings[m['tool_name']] = m

# helper function
def _add_tool_to_list(element, tool_list):
    children = element.getchildren()
    for child in children:
        s = tool_list
        tool_list = _add_tool_to_list(child, s)
    if element.tag == "tool":
        tool_list[element.attrib["id"]] = element.attrib["type"]
        return tool_list
    else:
        return tool_list

class Control:
    """ Main control class
    """
    def __init__(self, name=""):
        self.library = None
        if name == "":
            if platform.system() == "Windows":
               self.library  = ctypes.cdll.LoadLibrary("vidi_20.dll")
            else:
                self.library = ctypes.cdll.LoadLibrary("libvidi.so")
        else:
            self.library = ctypes.cdll.LoadLibrary(name)
        self.is_init = False

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinitialize()

    def __del__(self):
        self.deinitialize()
        del self.library


    def initialize(self, gpu_mode=GPUMode.single, cuda_devices=""):
        initialize = getattr(self.library, "vidi_initialize")
        result_t = initialize(gpu_mode.value, _vidi_str(cuda_devices))
        if not result_t == 0:
            raise RuntimeError("failed to initialize the library")
        self.is_init = True

    def deinitialize(self):
        if self.is_init:
            deinitialize = getattr(self.library, "vidi_deinitialize")
            result_t = deinitialize()
            if result_t:
                raise RuntimeError(self.get_error(result_t))
            self.is_init = False

    def open_workspace_from_file(self, ws_name, ws_path):
        open_workspace_from_file = getattr(self.library, "vidi_runtime_open_workspace_from_file")
        result_t = open_workspace_from_file(_vidi_str(ws_name), _vidi_str(ws_path))
        if result_t:
            raise RuntimeError(self.get_error(result_t))

    def close_workspace(self, ws_name):
        close_workspace = getattr(self.library, "vidi_runtime_close_workspace")
        c_ws_name = ctypes.c_char_p()
        c_ws_name.value = ws_name.encode("utf-8")
        result_t = close_workspace(c_ws_name)
        if result_t:
            raise RuntimeError("failed to close workspace")

    def list_compute_devices(self):
        with Buffer(self) as buffer:
            list_cuda_devices = getattr(self.library, "vidi_list_compute_devices")
            result_t = list_cuda_devices(buffer.pointer)
            if not result_t == 0:
                raise RuntimeError(self.get_error(result_t))
            v = str(buffer.pointer.contents.data, 'utf-8')
            cuda_device_list = ET.fromstring(v).findall("device")
            return [x.attrib['id'] for x in cuda_device_list]

    def get_error(self, error_number):
        with Buffer(self) as buffer:
            get_error_message = getattr(self.library, "vidi_get_error_message")
            result_t = get_error_message(error_number, buffer.pointer)
            if not result_t == 0:
                raise RuntimeError("failed to get error message")
            error_fragment = str(buffer.pointer.contents.data,'utf-8')
            message = ET.fromstring(error_fragment).text
            return message

    def debug_infos(self, sink_type=DebugSink.console, debug_file_path=""):
        # if 1 :
        with Buffer(self) as buffer:
            debug_infos = getattr(self.library, "vidi_debug_infos")
            if (sink_type == DebugSink.file and debug_file_path == ""):
                raise RuntimeError("you should provide a filename when using file as debug sink")

            result_t = debug_infos(sink_type.value, _vidi_str(debug_file_path))
            if not result_t == 0:
                raise RuntimeError(self.get_error(result_t))

    def stop_debug_infos(self):
        self.debug_infos(DebugSink.stop)

    def version(self):
        with Buffer(self) as buffer:
            version = getattr(self.library, "vidi_version")
            result_t = version(buffer.pointer)
            if not result_t == 0:
                raise RuntimeError(self.get_error(result_t))
            v = str(buffer.pointer.contents.data, 'utf-8')
            xml = ET.fromstring(v)
            return xml.attrib

    def init_buffer(self):
        vidi_buffer = ctypes.pointer(__Buffer__())
        init_buffer = getattr(self.library, "vidi_init_buffer")
        result_t = init_buffer(vidi_buffer)
        if not result_t == 0:
            raise RuntimeError("failed to allocate buffer")
        return vidi_buffer

    def free_buffer(self, vidi_buffer):
        free_buffer = getattr(self.library, "vidi_free_buffer")
        result_t = free_buffer(vidi_buffer)
        if not result_t == 0:
            raise RuntimeError(self.get_error(result_t))

    def list_workspaces(self):
        with Buffer(self) as buffer:
            list_workspaces = getattr(self.library, "vidi_runtime_list_workspaces")
            result_t = list_workspaces(buffer.pointer)
            if not result_t == 0:
                raise RuntimeError(self.get_error(result_t))
            v = str(buffer.pointer.contents.data, 'utf-8')
            ws_list = ET.fromstring(v).findall("workspace")
            return [x.attrib['id'] for x in ws_list]

    def list_streams(self, ws_name):
        with Buffer(self) as buffer:
            list_streams = getattr(self.library, "vidi_runtime_list_streams")

            result_t = list_streams(_vidi_str(ws_name), buffer.pointer)
            if not result_t == 0:
                raise RuntimeError(self.get_error(result_t))

            v = str(buffer.pointer.contents.data, 'utf-8')
            streams = ET.fromstring(v).findall("stream")
            return [x.attrib['id'] for x in streams]

    def list_tools(self, ws_name, stream_name):
        with Buffer(self) as buffer:
            list_tools = getattr(self.library, "vidi_runtime_list_tools")
            result_t = list_tools(_vidi_str(ws_name), _vidi_str(stream_name), buffer.pointer)
            if not result_t == 0:
                raise RuntimeError(self.get_error(result_t))
            v = str(buffer.pointer.contents.data, 'utf-8')
            l = {}
            l = _add_tool_to_list(ET.fromstring(v), l)
            return l

    def init_image(self):
        image_pointer = ctypes.pointer(Image())
        init_image_c = getattr(self.library, "vidi_init_image")
        result_t = init_image_c(image_pointer)
        if not result_t == 0:
            raise RuntimeError(self.get_error(result_t))
        return image_pointer

    def free_image(self, img):
        free_image = getattr(self.library, "vidi_free_image")
        result_t = free_image(img)
        if not result_t == 0:
            raise RuntimeError(self.get_error(result_t))

    def load_image(self, path):
        img = self.init_image()
        load_image = getattr(self.library, "vidi_load_image")
        result_t = load_image(_vidi_str(path), img)
        if not result_t == 0:
            raise RuntimeError(self.get_error(result_t))
        return img

    def save_image(self, path, img):
        save_image = getattr(self.library, "vidi_save_image")
        result_t = save_image(_vidi_str(path), img)
        if not result_t == 0:
            raise RuntimeError(self.get_error(result_t))

    def process(self, c_img, ws_name, stream_name="default", tool_name="", sample_name="0", parameters="all_tools", gpu_list=""):
        with Buffer(self) as buffer:
            process = getattr(self.library, "vidi_runtime_process")
            result_t = process(c_img,
                               _vidi_str(ws_name),
                               _vidi_str(stream_name),
                               _vidi_str(tool_name),
                               _vidi_str(sample_name),
                               _vidi_str(parameters),
                               _vidi_str(gpu_list),
                               buffer.pointer)

            if not result_t == 0:
                raise RuntimeError(self.get_error(result_t))

            buffer_str = str(buffer.pointer.contents.data,'utf-8')
            return Sample(buffer_str)

    def get_overlay(self, workspace_name, stream_name, tool_name, sample_name="0", view_index=-1, options=""):
        overlay_image = self.init_image()
        get_overlay = getattr(self.library, "vidi_runtime_get_overlay")

        result_t = get_overlay(
                _vidi_str(workspace_name),
                _vidi_str(stream_name),
                _vidi_str(tool_name),
                _vidi_str(sample_name),
                view_index,
                _vidi_str(options),
                overlay_image)

        if not result_t == 0:
            raise RuntimeError(self.get_error(result_t))

        return overlay_image