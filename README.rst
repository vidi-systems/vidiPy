Python wrapper around ViDi Runtime API
=========================

How to use : 

.. code-block:: python

	>>> import vidi
	>>> # load the dll
	>>> control = vidi.Runtime() 
	>>> # enable debug infos from C library
	>>> control = vidi.debug_infos()
	>>>	#initialize the control
	>>> control.initialize(gpu_mode = vidi.GPUMode.single)
	>>> devices = control.list_compute_devices()
	>>>	print(devices)
	>>> control.open_workspace_from_file(ws_name = "dials",ws_path =  "dials.vrws")
	>>> control.list_workspaces()
	>>> ...

Installation
------------

To install ViDiPy, simply follow the following instructions:


.. code-block:: bash

	$ cd vidiPy
	$ python setup.py sdist
	$ cd dist
	$ pip install vidi-2.0.0.zip


Documentation
-------------

https://customer-space.vidi-systems.com/api_documentation_20_c.html

