import tracemalloc
import numpy as np


class MemoryThresholdExceeded(Exception):
    pass


class MemoryThreshold:
    """
    Context manager to check peak memory usage against an expected threshold.

    example usage:
    with MemoryThreshold(expected_usage):
        # code that should not exceed expected
    
    If the code in the with statement uses more than the expected_usage
    memory (in bytes) a ``MemoryThresholdExceeded`` exception
    will be raised.
    
    Note that this class does not prevent allocations beyond the threshold
    and only checks the actual peak allocations to the threshold at the
    end of the with statement.
    """

    def __init__(self, expected_usage):
        """
        Parameters
        ----------
        expected_usage : list
            Expected peak memory usage (integer) and units (string, e.g. 'MB', 'GB')
        """
        self.expected_usage = expected_usage

    def __enter__(self):
        tracemalloc.start()
        return self

    def pretty_size(self, bytes, inunits=None, outunits=None):
        """Get human-readable file sizes.
        simplified version of https://pypi.python.org/pypi/hurry.filesize/

        Parameters
        ----------
        bytes : int
            Input from tracemalloc generally

        inunits: str
            In case the input is in other units

        outunits : str
            Units for the output

        Returns
        -------
        output : list
            The converted units (float) and the corresponding unit (string)

        """
        # bytes pretty-printing
        units_map = [
            (1 << 50, ' PB'),
            (1 << 40, ' TB'),
            (1 << 30, ' GB'),
            (1 << 20, ' MB'),
            (1 << 10, ' KB'),
            (1, (' byte', ' bytes')),
        ]
        if inunits is not None:
            for i, item in enumerate(units_map):
                if inunits in item[1]:
                    stop_at_idx = i
                    break
            units_map = [item for i, item in enumerate(units_map) if i <= stop_at_idx]
            bytes = float(bytes * item[0])

        for factor, suffix in units_map:
            if outunits is None:
                if bytes >= factor:
                    break
            elif outunits == suffix.strip():
                break

        amount = bytes / factor

        if isinstance(suffix, tuple):
            singular, multiple = suffix
            if amount == 1:
                suffix = singular
            else:
                suffix = multiple
        output = [np.round(amount, decimals=1), suffix]
        return output

    def __exit__(self, exc_type, exc_value, traceback):
        # convert the expected memory to bytes
        expected_usage, units = self.expected_usage
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak, peakunits = self.pretty_size(peak, outunits=units)

        if peak > expected_usage:
            msg = ("Peak memory usage exceeded expected usage: "
                   f"{peak} {peakunits} > {expected_usage} {units}")
            raise MemoryThresholdExceeded(msg)
