Python wrapper around ViDi Runtime API
=========================

Behold, the power of Requests:

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
..

Installation
------------

To install ViDiPy, simply:

.. code-block:: bash
	$ cd vidiPy
    $ python package setup.py sdist
    $ cd dist
	$ pip install vidi-2.0.0.zip
..