"""A profiler context manager for Earth Engine Python API."""
from __future__ import annotations

import io
import re

import ee
from anyascii import anyascii

from .accessors import _register_extention


@_register_extention(ee.geetools)
class Profiler:
    """A profiler context manager for Earth Engine Python API.

    Examples:
        .. jupyter-execute::

            import ee, geetools
            from geetools.utils import initialize_documentation

            initialize_documentation()

            with ee.geetools.Profiler() as p:
                ee.Number(3.14).add(0.00159).getInfo()
                res = p.profile
            res
    """

    _output_capture: io.StringIO | None = None
    "The output of the profiler."

    _profile_context: ee.profilePrinting | None = None
    "The raw profile context."

    profile: dict | None = None
    "The profile data as a dictionary."

    def __enter__(self):
        """Enter the context manager."""
        self._output_capture = io.StringIO()
        self._profile_context = ee.profilePrinting(destination=self._output_capture)
        self._profile_context.__enter__()
        return self

    def __exit__(self, *args):
        """Exit the context manager."""
        self._profile_context.__exit__(*args)

        # Check if there's anything captured
        profile_output = self._output_capture.getvalue()
        if profile_output:
            self.profile = self._to_dict(profile_output)
        else:
            self.profile = None  # Handle the case where no output is captured
            print("Warning: No profile output was captured.")

        self._output_capture.close()

    def _memory(self, mem_str: str) -> int:
        """Transform a memory string to an integer."""
        mapping = {"": 1, "k": 3, "M": 6, "G": 9, "T": 12}

        # Match numbers with optional multipliers (k, M, etc.)
        # and apply the multiplier to the number
        match = re.match(r"([\d.]+)([kMGT]?)", mem_str)
        if match is None:
            raise ValueError(f"Invalid memory string: {mem_str}")

        number, multiplier = float(match.group(1)), match.group(2)

        return int(number * 10 ** mapping[multiplier])

    def _to_dict(self, input: str) -> dict:
        """Transform the output of an Earthengine profiler into a dictionary compatible with pandas DataFrame."""
        # Split the string into lines
        lines = input.strip().splitlines()

        # First line contains column headers
        # Initialize a dictionary to hold lists for each column
        headers = [anyascii(h.strip()) for h in lines[0].split()]
        result: dict = {header: [] for header in headers}
        # functions to process/format each header
        process = {
            "EECU-s": lambda eecus: float(eecus) if eecus != "-" else None,
            "CurrMem": lambda mem: self._memory(mem),  # Mem is a string to convert
            "PeakMem": lambda mem: self._memory(mem),  # Mem is a string to convert
            "Count": lambda count: int(count),  # Count is an integer
            "Description": lambda desc: " ".join(desc)
            if isinstance(desc, list)
            else desc,  # Description can have multiple words
        }

        # Process each line of data after the header
        for line in lines[1:]:
            # Split the line by spaces, considering multiple spaces as a separator
            # Handle missing values denoted by "-"
            parts = line.split()
            part_result = dict(zip(headers, parts))
            # Populate the dictionary with values for each column
            for head in headers:
                result[head].append(process[head](part_result[head]))
        return result
