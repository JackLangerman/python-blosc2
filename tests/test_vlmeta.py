########################################################################
#
#       Author:  The Blosc development team - blosc@blosc.org
#
########################################################################

import numpy
import pytest

import blosc2


@pytest.mark.parametrize("contiguous", [True, False])
@pytest.mark.parametrize("urlpath", [None, "b2frame"])
@pytest.mark.parametrize(
    "cparams, dparams, nchunks",
    [
        ({"compcode": blosc2.Codec.LZ4, "clevel": 6, "typesize": 4}, {}, 10),
    ],
)
def test_schunk_numpy(contiguous, urlpath, cparams, dparams, nchunks):
    storage = {"contiguous": contiguous, "urlpath": urlpath, "cparams": cparams, "dparams": dparams}
    blosc2.remove_urlpath(urlpath)

    schunk = blosc2.SChunk(chunksize=200 * 1000 * 4, **storage)
    for i in range(nchunks):
        buffer = i * numpy.arange(200 * 1000, dtype="int32")
        nchunks_ = schunk.append_data(buffer)
        assert nchunks_ == (i + 1)

    add(schunk)
    iter(schunk)
    delete(schunk)
    clear(schunk)

    blosc2.remove_urlpath(urlpath)


@pytest.mark.parametrize("contiguous", [True, False])
@pytest.mark.parametrize("urlpath", [None, "b2frame"])
@pytest.mark.parametrize(
    "nbytes, cparams, dparams, nchunks",
    [
        (136, {"compcode": blosc2.Codec.LZ4, "clevel": 6, "typesize": 1}, {}, 10),
    ],
)
def test_schunk(contiguous, urlpath, nbytes, cparams, dparams, nchunks):
    storage = {"contiguous": contiguous, "urlpath": urlpath, "cparams": cparams, "dparams": dparams}

    blosc2.remove_urlpath(urlpath)
    schunk = blosc2.SChunk(chunksize=2 * nbytes, **storage)
    for i in range(nchunks):
        bytes_obj = b"i " * nbytes
        nchunks_ = schunk.append_data(bytes_obj)
        assert nchunks_ == (i + 1)

    add(schunk)
    iter(schunk)
    delete(schunk)
    clear(schunk)

    blosc2.remove_urlpath(urlpath)


def add(schunk):
    schunk.vlmeta["vlmeta1"] = b"val1"
    schunk.vlmeta["vlmeta2"] = "val2"
    schunk.vlmeta["vlmeta3"] = {b"lorem": 4231}

    assert schunk.vlmeta["vlmeta1"] == b"val1"
    assert schunk.vlmeta["vlmeta2"] == "val2"
    assert schunk.vlmeta["vlmeta3"] == {b"lorem": 4231}
    assert "vlmeta1" in schunk.vlmeta
    assert len(schunk.vlmeta) == 3


def delete(schunk):
    # Remove one of them
    assert('vlmeta2' in schunk.vlmeta)
    del schunk.vlmeta['vlmeta2']
    assert 'vlmeta2' not in schunk.vlmeta
    assert(schunk.vlmeta['vlmeta1'] == b'val1')
    assert(schunk.vlmeta['vlmeta3'] == {b"lorem": 4231})
    with pytest.raises(KeyError):
        schunk.vlmeta['vlmeta2']
    assert(len(schunk.vlmeta) == 2)


def iter(schunk):
    keys = ["vlmeta1", "vlmeta2", "vlmeta3"]
    i = 0
    for vlmeta in schunk.vlmeta:
        assert vlmeta == keys[i]
        i += 1


def clear(schunk):
    nparray = numpy.arange(start=0, stop=2)
    schunk.vlmeta["vlmeta2"] = nparray.tobytes()
    assert schunk.vlmeta["vlmeta2"] == nparray.tobytes()
    assert schunk.vlmeta.__len__() == 3

    schunk.vlmeta.clear()
    assert schunk.vlmeta.__len__() == 0
