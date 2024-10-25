"""Test the ee_profiler module."""
import ee

import geetools  # noqa: F401


class TestProfiler:
    """Test the Profiler class."""

    def test_profiler(self):
        """Test the Profiler class."""

    with ee.geetools.Profiler() as p:
        ee.Number(3.14).add(0.00159).getInfo()
    assert [k for k in p.profile] == ["EECU-s", "PeakMem", "Count", "Description"]
