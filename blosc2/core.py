########################################################################
#
#       Author:  The Blosc development team - blosc@blosc.org
#
########################################################################


import os
import pickle
import sys

import blosc2
from blosc2 import blosc2_ext


def _check_typesize(typesize):
    if not 1 <= typesize <= blosc2_ext.MAX_TYPESIZE:
        raise ValueError("typesize can only be in the 1-%d range." % blosc2_ext.MAX_TYPESIZE)


def _check_clevel(clevel):
    if not 0 <= clevel <= 9:
        raise ValueError("clevel can only be in the 0-9 range.")


def _check_input_length(input_name, input_len, typesize, _ignore_multiple_size=False):
    if input_len > blosc2_ext.MAX_BUFFERSIZE:
        raise ValueError("%s cannot be larger than %d bytes" % (input_name, blosc2_ext.MAX_BUFFERSIZE))
    if not _ignore_multiple_size and input_len % typesize != 0:
        raise ValueError("len(%s) can only be a multiple of typesize (%d)." % (input_name, typesize))


def _check_filter(filter):
    if filter not in blosc2.Filter:
        raise ValueError(
            "filter can only be one of ", blosc2.Filter.keys()
        )


def _check_codec(codec):
    if codec not in blosc2.Codec:
        raise ValueError("codec can only be one of: %s, not '%s'" % (codecs, codec))


def compress(src, typesize=None, clevel=9, filter=blosc2.Filter.SHUFFLE, codec=blosc2.Codec.BLOSCLZ,
             _ignore_multiple_size=False):
    """Compress src, with a given type size.

    Parameters
    ----------
    src : bytes-like object (supporting the buffer interface)
        The data to be compressed.
    typesize : int (optional) from 1 to 255
        The data type size. The default is 1, or `src.itemsize` if it exists.
    clevel : int (optional)
        The compression level from 0 (no compression) to 9
        (maximum compression).  The default is 9.
    filter : :class:`Filter` (optional)
        The filter to be activated. The
        default is :py:obj:`Filter.SHUFFLE <Filter>`.
    codec : :class:`Codec` (optional)
        The compressor used internally in Blosc. The default is :py:obj:`Codec.BLOSCLZ <Codec>`.

    Returns
    -------
    out : str / bytes
        The compressed data in form of a Python str / bytes object.

    Raises
    ------
    TypeError
        If :paramref:`src` doesn't support the buffer interface.
    ValueError
        If :paramref:`src` is too long.
        If :paramref:`typesize` is not within the allowed range.
        If :paramref:`clevel` is not within the allowed range.
        If :paramref:`codec` is not within the supported compressors.

    Notes
    -----
    The `cname` and `shuffle` parameters in python-blosc API have been replaced by :paramref:`codec` and
    :paramref:`filter` respectively.
    To set :paramref:`codec` and :paramref:`fitler`, the enumerates :class:`Codec` and :class:`Filter`
    have to be used instead of the python-blosc API variables such as `blosc.SHUFFLE` for :paramref:`filter`
    or strings like "blosclz" for :paramref:`codec`.

    Examples
    --------
    >>> import array, sys
    >>> a = array.array('i', range(1000*1000))
    >>> a_bytesobj = a.tobytes()
    >>> c_bytesobj = blosc2.compress(a_bytesobj, typesize=4)
    >>> len(c_bytesobj) < len(a_bytesobj)
    True
    """
    len_src = len(src)
    if hasattr(src, "itemsize"):
        if typesize is None:
            typesize = src.itemsize
        len_src *= src.itemsize
    else:
        # Let's not guess the typesize for non NumPy objects
        if typesize is None:
            typesize = 1
    _check_clevel(clevel)
    _check_typesize(typesize)
    _check_filter(filter)
    _check_input_length("src", len_src, typesize, _ignore_multiple_size=_ignore_multiple_size)
    return blosc2_ext.compress(src, typesize, clevel, filter, codec)


def decompress(src, dst=None, as_bytearray=False):
    """Decompresses a bytes-like compressed object.

    Parameters
    ----------
    src : bytes-like object
        The data to be decompressed.  Must be a bytes-like object
        that supports the Python Buffer Protocol, like bytes, bytearray,
        memoryview, or `numpy.ndarray <https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html>`_.
    dst : NumPy object or bytearray
        The destination NumPy object or bytearray to fill,
        the length of which must be greater than 0.
        The user must make sure
        that it has enough capacity for hosting the decompressed data.
        Default is None, meaning that a new `bytes` or `bytearray` object
        is created, filled and returned.
    as_bytearray : bool (optional)
        If this flag is True then the return type will be a bytearray object
        instead of a bytes object.

    Returns
    -------
    out: str/bytes or bytearray
        If :paramref:`dst` is `None`, the decompressed data in form of a Python str / bytes object.
        If as_bytearray is True then this will be a bytearray object.

        If :paramref:`dst` is not `None`, it will return `None` because the result
        will already be in :paramref:`dst`.

    Raises
    ------
    RuntimeError
        The compressed data is corrupted or the output buffer is not large enough.
        Could not get a bytes object.
    TypeError
        If :paramref:`src` does not support Buffer Protocol.
    ValueError
        If the length of :paramref:`src` is smaller than the minimum.
        If :paramref:`dst` is not None and its length is 0.

    Examples
    --------
    >>> import array, sys
    >>> a = array.array('i', range(1000*1000))
    >>> a_bytesobj = a.tobytes()
    >>> c_bytesobj = blosc2.compress(a_bytesobj, typesize=4)
    >>> a_bytesobj2 = blosc2.decompress(c_bytesobj)
    >>> a_bytesobj == a_bytesobj2
    True
    >>> b"" == blosc2.decompress(blosc2.compress(b""))
    True
    >>> b"1"*7 == blosc2.decompress(blosc2.compress(b"1"*7))
    True
    >>> type(blosc2.decompress(blosc2.compress(b"1"*7),
    ...                                      as_bytearray=True)) is bytearray
    True
    >>> import numpy
    >>> arr = numpy.arange(10)
    >>> comp_arr = blosc2.compress(arr)
    >>> dest = numpy.empty(arr.shape, arr.dtype)
    >>> blosc2.decompress(comp_arr, dst=dest)
    >>> numpy.array_equal(arr, dest)
    True
    """
    return blosc2_ext.decompress(src, dst, as_bytearray)


def pack(obj, clevel=9, filter=blosc2.Filter.SHUFFLE, codec=blosc2.Codec.BLOSCLZ):
    """Pack (compress) a Python object.

    Parameters
    ----------
    obj : Python object  with `itemsize` attribute
        The Python object to be packed.
    clevel : int (optional)
        The compression level from 0 (no compression) to 9
        (maximum compression).  The default is 9.
    filter : :class:`Filter` (optional)
        The filter to be activated. The
        default is :py:obj:`Filter.SHUFFLE <Filter>`.
    codec : :class:`Codec` (optional)
        The compressor used internally in Blosc. The default is
        :py:obj:`Codec.BLOSCLZ <Codec>`.

    Returns
    -------
    out : str / bytes
        The packed object in form of a Python str / bytes object.

    Raises
    ------
    AttributeError
        If :paramref:`obj` does not have an `itemsize` attribute.
        If :paramref:`obj` does not have an `size` attribute.
    ValueError
        If the pickled object size is larger than the maximum allowed buffer size.
        If typesize is not within the allowed range.
        If :paramref:`clevel` is not within the allowed range.
        If :paramref:`codec` is not within the supported compressors.

    Notes
    -----
    The `cname` and `shuffle` parameters in python-blosc API have been replaced by :paramref:`codec` and
    :paramref:`filter` respectively.
    To set :paramref:`codec` and :paramref:`fitler`, the enumerates :class:`Codec` and :class:`Filter`
    have to be used instead of the python-blosc API variables such as `blosc.SHUFFLE` for :paramref:`filter`
    or strings like "blosclz" for :paramref:`codec`.

    Examples
    --------
    >>> import numpy
    >>> a = numpy.arange(1e6)
    >>> parray = blosc2.pack(a)
    >>> len(parray) < a.size*a.itemsize
    True
    """
    if not hasattr(obj, "itemsize"):
        raise AttributeError("The object must have an itemsize attribute.")
    if not hasattr(obj, "size"):
        raise AttributeError("The object must have an size attribute.")
    else:
        itemsize = obj.itemsize
        _check_clevel(clevel)
        _check_codec(codec)
        _check_typesize(itemsize)
        pickled_object = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
        # The object to be compressed is pickled_object, and not obj
        len_src = len(pickled_object)
        _check_input_length("pickled object", len_src, itemsize, _ignore_multiple_size=True)
        packed_object = compress(pickled_object, typesize=itemsize, clevel=clevel,
                                 filter=filter, codec=codec, _ignore_multiple_size=True)
    return packed_object


def unpack(packed_object, **kwargs):
    """Unpack (decompress) an object.

    Parameters
    ----------
    packed_object : str / bytes
        The packed object to be decompressed.
    **kwargs : fix_imports / encoding / errors
        Optional parameters that can be passed to the
        `pickle.loads API <https://docs.python.org/3/library/pickle.html#pickle.loads>`_

    Returns
    -------
    out : object
        The decompressed data in form of the original object.

    Raises
    ------
    TypeError
        If :paramref:`packed_object` is not of type bytes or string.

    Examples
    --------
    >>> import numpy
    >>> a = numpy.arange(1e6)
    >>> parray = blosc2.pack(a)
    >>> len(parray) < a.size*a.itemsize
    True
    >>> a2 = blosc2.unpack(parray)
    >>> numpy.array_equal(a, a2)
    True
    >>> a = numpy.array(['å', 'ç', 'ø'])
    >>> parray = blosc2.pack(a)
    >>> a2 = blosc2.unpack(parray)
    >>> numpy.array_equal(a, a2)
    True
    """
    pickled_object = decompress(packed_object)
    if kwargs:
        obj = pickle.loads(pickled_object, **kwargs)
    else:
        obj = pickle.loads(pickled_object)

    return obj


def pack_array(arr, clevel=9, filter=blosc2.Filter.SHUFFLE, codec=blosc2.Codec.BLOSCLZ):
    """Pack (compress) a NumPy array. It is equivalent to the pack function.

    Parameters
    ----------
    arr : ndarray
        The NumPy array to be packed.
    clevel : int (optional)
        The compression level from 0 (no compression) to 9
        (maximum compression).  The default is 9.
    filter : :class:`Filter` (optional)
        The filter to be activated. The
        default is :py:obj:`Filter.SHUFFLE <Filter>`.
    codec : :class:`Codec` (optional)
        The compressor used internally in Blosc. The default is
        :py:obj:`Codec.BLOSCLZ <Codec>`.

    Returns
    -------
    out : str / bytes
        The packed array in form of a Python str / bytes object.

    Raises
    ------
    AttributeError
        If :paramref:`arr` does not have an `itemsize` attribute.
        If :paramref:`arr` does not have a `size` attribute.
    ValueError
        If typesize is not within the allowed range.
        If the pickled object size is larger than the maximum allowed buffer size.
        If :paramref:`clevel` is not within the allowed range.
        If :paramref:`codec` is not within the supported compressors.

    See also
    --------
    :func:`~blosc2.pack`

    Examples
    --------
    >>> import numpy
    >>> a = numpy.arange(1e6)
    >>> parray = blosc2.pack_array(a)
    >>> len(parray) < a.size*a.itemsize
    True
    """
    return pack(arr, clevel, filter, codec)


def unpack_array(packed_array, **kwargs):
    """Unpack (decompress) a packed NumPy array.

    Parameters
    ----------
    packed_array : str / bytes
        The packed array to be decompressed.
    **kwargs : fix_imports / encoding / errors
        Optional parameters that can be passed to the
        `pickle.loads API <https://docs.python.org/3/library/pickle.html#pickle.loads>`_.

    Returns
    -------
    out : ndarray
        The decompressed data in form of a NumPy array.

    Raises
    ------
    TypeError
        If :paramref:`packed_array` is not of type bytes or string.

    Examples
    --------
    >>> import numpy
    >>> a = numpy.arange(1e6)
    >>> parray = blosc2.pack_array(a)
    >>> len(parray) < a.size*a.itemsize
    True
    >>> a2 = blosc2.unpack_array(parray)
    >>> numpy.array_equal(a, a2)
    True
    >>> a = numpy.array(['å', 'ç', 'ø'])
    >>> parray = blosc2.pack_array(a)
    >>> a2 = blosc2.unpack_array(parray)
    >>> numpy.array_equal(a, a2)
    True
    """
    pickled_array = decompress(packed_array)
    if kwargs:
        arr = pickle.loads(pickled_array, **kwargs)
        if all(isinstance(x, bytes) for x in arr.tolist()):
            import numpy

            arr = numpy.array([x.decode("utf-8") for x in arr.tolist()])
    else:
        arr = pickle.loads(pickled_array)

    return arr


def set_compressor(codec):
    """Set the compressor to be used. If this function is not
    called, then :py:obj:`blosc2.Codec.BLOSCLZ <Codec>` will be used.

    Parameters
    ----------
    codec : :class:`Codec`
        The compressor to be used.

    Returns
    -------
    out : int
        The code for the compressor (>=0).

    Raises
    ------
    ValueError
        If the compressor is not recognized, or there is not support for it.

    Notes
    -----
    The `compname` parameter in python-blosc API has been replaced by :paramref:`codec` , using `compname`
    as parameter or a string as a :paramref:`codec` value will not work.
    """
    return blosc2_ext.set_compressor(codec)


def free_resources():
    """Free possible memory temporaries and thread resources.

    Returns
    -------
        out : None

    Notes
    -----
    Blosc maintain a pool of threads waiting for work as well as some
    temporary space.  You can use this function to release these
    resources when you are not going to use Blosc for a long while.

    Examples
    --------
    >>> blosc2.free_resources()
    """
    blosc2_ext.free_resources()


def set_nthreads(nthreads):
    """Set the number of threads to be used during Blosc operation.

    Parameters
    ----------
    nthreads : int
        The number of threads to be used during Blosc operation.

    Returns
    -------
    out : int
        The previous number of used threads.

    Raises
    ------
    ValueError
        If :paramref:`nthreads` is larger than the maximum number of threads blosc can use.
        If :paramref:`nthreads` is not a positive integer.

    Notes
    -----
    The maximum number of threads for Blosc is :math:`2^{31} - 1`. In some
    cases Blosc gets better results if you set the number of threads
    to a value slightly below than your number of cores
    (via :func:`~blosc2.detect_number_of_cores`).

    Examples
    --------
    Set the number of threads to 2 and then to 1:
    >>> oldn = blosc2.set_nthreads(2)
    >>> blosc2.set_nthreads(1)
    2
    """
    blosc2.nthreads = nthreads
    return blosc2_ext.set_nthreads(nthreads)


def compressor_list():
    """
    Returns a list of compressors available in C library.

    Returns
    -------
    out : list
        The list of names.
    """
    return list(key.lower() for key in blosc2.Codec.__members__.keys())


def set_blocksize(blocksize=0):
    """
    Force the use of a specific blocksize.  If 0, an automatic
    blocksize will be used (the default).

    Notes
    -----
    This is a low-level function and is recommended for expert users only.

    Examples
    --------
    >>> blosc2.set_blocksize(512)
    >>> blosc2.set_blocksize(0)
    """
    return blosc2_ext.set_blocksize(blocksize)


def clib_info(codec):
    """Return info for compression libraries in C library.

    Parameters
    ----------
    codec : :class:`Codec`
        The compressor.

    Returns
    -------
    out : tuple
        The associated library name and version.

    Notes
    -----
    The `cname` parameter in python-blosc API has been replaced by :paramref:`codec` , using `cname`
    as parameter or a string as a :paramref:`codec` value will not work.
    """
    return blosc2_ext.clib_info(codec)


def get_clib(bytesobj):
    """
    Return the name of the compression library for Blosc :paramref:`bytesobj` buffer.

    Parameters
    ----------
    bytesobj : str / bytes
        The compressed buffer.

    Returns
    -------
    out : str
        The name of the compression library.
    """
    return blosc2_ext.get_clib(bytesobj).decode()


def get_compressor():
    """Get the current compressor that is used for compression.

    Returns
    -------
    out : str
        The name of the compressor.
    """
    return blosc2_ext.get_compressor().decode()


def set_releasegil(gilstate):
    """
    Sets a boolean on whether to release the Python global inter-lock (GIL)
    during c-blosc compress and decompress operations or not.  This defaults
    to False.

    Parameters
    ----------
    gilstate: bool
        True to release the GIL

    Notes
    -----
    Designed to be used with larger chunk sizes and a ThreadPool.  There is a
    small performance penalty with releasing the GIL that will more harshly
    penalize small block sizes.

    Examples
    --------
    >>> oldReleaseState = blosc2.set_releasegil(True)
    """
    gilstate = bool(gilstate)
    return blosc2_ext.set_releasegil(gilstate)


def detect_number_of_cores():
    """Detect the number of cores in this system.

    Returns
    -------
    out : int
        The number of cores in this system.
    """
    # Linux, Unix and MacOS:
    if hasattr(os, "sysconf"):
        if "SC_NPROCESSORS_ONLN" in os.sysconf_names:
            # Linux & Unix:
            ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
            if isinstance(ncpus, int) and ncpus > 0:
                return ncpus
        else:  # OSX:
            return int(os.popen2("sysctl -n hw.ncpu")[1].read())
    # Windows:
    if "NUMBER_OF_PROCESSORS" in os.environ:
        ncpus = int(os.environ["NUMBER_OF_PROCESSORS"])
        if ncpus > 0:
            return ncpus
    return 1  # Default


# Dictionaries for the maps between compressor names and libs
codecs = compressor_list()
# Map for compression libraries and versions
clib_versions = {}
for codec, value in blosc2.Codec.__members__.items():
    clib_versions[codec] = clib_info(value)[1].decode()


def os_release_pretty_name():
    for p in ("/etc/os-release", "/usr/lib/os-release"):
        try:
            f = open(p, "rt")
            for line in f:
                name, _, value = line.rstrip().partition("=")
                if name == "PRETTY_NAME":
                    if len(value) >= 2 and value[0] in "\"'" and value[0] == value[-1]:
                        value = value[1:-1]
                    return value
        except IOError:
            pass
        finally:
            f.close()
    return None


def print_versions():
    """Print all the versions of software that python-blosc2 relies on."""
    import platform

    print("-=" * 38)
    print("python-blosc2 version: %s" % blosc2.__version__)
    print("Blosc version: %s" % blosc2.blosclib_version)
    print("Compressors available: %s" % codecs)
    print("Compressor library versions:")
    for clib in sorted(clib_versions.keys()):
        print("  %s: %s" % (clib, clib_versions[clib]))
    print("Python version: %s" % sys.version)
    (sysname, nodename, release, version, machine, processor) = platform.uname()
    print("Platform: %s-%s-%s (%s)" % (sysname, release, machine, version))
    if sysname == "Linux":
        distro = os_release_pretty_name()
        if distro:
            print("Linux dist:", distro)
    if not processor:
        processor = "not recognized"
    print("Processor: %s" % processor)
    print("Byte-ordering: %s" % sys.byteorder)
    # Internal Blosc threading
    print("Detected cores: %s" % blosc2.ncores)
    print("Number of threads to use by default: %s" % blosc2.nthreads)
    print("-=" * 38)


def get_blocksize():
    """Get the internal blocksize to be used during compression.

    Returns
    -------
    out : int
        The size in bytes of the internal block size.
    """
    return blosc2_ext.get_blocksize()


def compress2(src, **kwargs):
    """Compress :paramref:`src` with the given compression params (if given)

    Parameters
    ----------
    src: bytes-like object (supporting the buffer interface)

    Other Parameters
    ----------------
    kwargs: dict, optional
        Keyword arguments supported:

            codec: :class:`Codec`
                The compressor code. Default is :py:obj:`Codec.BLOSCLZ <Codec>`.
            codec_meta: int
                The metadata for the compressor code, 0 by default.
            clevel: int
                The compression level from 0 (no compression) to 9
                (maximum compression). By default: 5.
            use_dict: bool
                Use dicts or not when compressing (only for :py:obj:`blosc2.Codec.ZSTD <Codec>`). By default `False`.
            typesize: int from 1 to 255
                The data type size. By default: 8.
            nthreads: int
                The number of threads to use internally (1 by default).
            blocksize: int
                The requested size of the compressed blocks. If 0 (the default)
                blosc2 chooses it automatically.
            splitmode: :class:`SplitMode`
                The split mode for the blocks.
                The default value is :py:obj:`SplitMode.FORWARD_COMPAT_SPLIT <SplitMode>`.
            filters: :class:`Filter` list
                The sequence of filters. By default: {0, 0, 0, 0, 0, :py:obj:`Filter.SHUFFLE <Filter>`}.
            filters_meta: list
                The metadata for filters. By default: `{0, 0, 0, 0, 0, 0}`.

    Returns
    -------
    out: str/bytes
        The compressed data in form of a Python str / bytes object.

    Raises
    ------
    RuntimeError
        If the data cannot be compressed into `dst`.
        If an internal error occurred, probably because some
        parameter is not a valid parameter.
    """
    return blosc2_ext.compress2(src, **kwargs)


def decompress2(src, dst=None, **kwargs):
    """Compress :paramref:`src` with the given compression params (if given)

    Parameters
    ----------
    src: bytes-like object
        The data to be decompressed. Must be a bytes-like object
        that supports the Python Buffer Protocol, like bytes,
        bytearray, memoryview, or numpy.ndarray.
    dst: NumPy object or bytearray
        The destination NumPy object or bytearray to fill, the length
        of which must be greater than 0. The user must make sure
        that it has enough capacity for hosting the decompressed
        data. Default is `None`, meaning that a new bytes object
        is created, filled and returned.

    Other Parameters
    ----------------
    kwargs: dict, optional
        Keyword arguments supported:
        nthreads: int
        The number of threads to use internally (1 by default).

    Returns
    -------
    out: str/bytes
        The decompressed data in form of a Python str / bytes object if
        :paramref:`dst` is `None`. Otherwise, it will return `None` because the result
        will already be in :paramref:`dst`.

    Raises
    ------
    RuntimeError
        If the data cannot be compressed into :paramref:`dst`.
        If an internal error occurred, probably because some
        parameter is not a valid one.
        If :paramref:`dst` is `None` and could not create a bytes object to store the result.
    TypeError
        If :paramref:`src` does not support the Buffer Protocol.
    ValueError
        If the length of :paramref:`src` is smaller than the minimum.
        If :paramref:`dst` is not None and its length is 0.
    """
    return blosc2_ext.decompress2(src, dst, **kwargs)


# Directory utilities
def remove_urlpath(path):
    """Permanently remove the file or the directory given by :paramref:`path`. This function is used during
    the tests of a persistent SChunk to remove it.

    Parameters
    ----------
    path: String
        The path of the directory or file.

    Returns
    -------
    None
    """
    if path is not None:
        path = path.encode("utf-8") if isinstance(path, str) else path
        blosc2_ext.remove_urlpath(path)
