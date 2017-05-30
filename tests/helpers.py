import io
import numpy as np

# ARGH: https://github.com/pytest-dev/pytest/issues/2180
# See test for usage

class BytesIOWrapper():
    """Minimal file-like object which wraps a :class:`io.BytesIO` instance
    internally, and grabs a copy of the buffer before it closes.  You may need
    to add methods as necessary to make this more usable.
    """
    def __init__(self):
        self._del = io.BytesIO()

    def write(self, *args):
        self._del.write(*args)

    def __enter__(self):
        return self._del.__enter__()

    def __exit__(self, a, b, c):
        self.data = self._del.getvalue()
        self._del.__exit__(a, b, c)

    def close(self):
        self.data = self._del.getvalue()
        self._del.close()


class MockOpen():
    """Mock out the builtin function :func:`open`.  Typical usage is:

        with mock.patch("builtins.open", MockOpen("1234")) as open_mock:
            with open("somefile.txt") as file:
                assert next(file) == "1234"

    You may also pass a `bytes` object instead of a string.

    The default :attr:`filter` only mocks out the first call to `open`.  This
    is important to make sure that e.g. `pytest` can load source code files in
    the event of a test failure...

    :param string_data: `str` or `bytes` object of data to return as the file
      contents.  May also be a file-like object to be directly returned, in
      which case 
    """
    def __init__(self, string_data):
        self._original_open = open
        self.data = string_data
        self.filter = FirstOnlyMockOpenFilter()
        self._calls = []

    def __call__(self, *args, **kwargs):
        if self.filter(args, kwargs):
            self.calls.append((args, kwargs))
            if isinstance(self.data, bytes):
                return io.BytesIO(self.data)
            elif isinstance(self.data, str):
                return io.StringIO(self.data)
            else:
                return self.data
        return self._original_open(*args, **kwargs)

    @property
    def calls(self):
        return self._calls


class FirstOnlyMockOpenFilter():
    def __init__(self, cases_to_filter = 1):
        self.count = 0
        self.cases_to_filter = cases_to_filter

    def __call__(self, *args, **kwargs):
        self.count += 1
        return self.count <= self.cases_to_filter


class ExactlyTheseFilter():
    def __init__(self, cases):
        self.count = 0
        self.cases = cases

    def __call__(self, *args, **kwargs):
        self.count += 1
        return self.count in self.cases


class RandomCyclicBuffer():
    def __init__(self, numbers):
        self._numbers = numbers
        self.offset = -1
        
    def _one_dimensional_array(self, length):
        out = np.empty(length)
        for i in range(length):
            self.offset += 1
            if self.offset == len(self._numbers):
                self.offset = 0
            out[i] = self._numbers[self.offset]
        return out
        
    def __call__(self, size=None):
        if size is None:
            return self._one_dimensional_array(1)[0]
        return self._one_dimensional_array(np.prod(size)).reshape(size)