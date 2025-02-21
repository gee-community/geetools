"""test the Number class methods."""
import geetools  # noqa: F401


class TestTruncate:
    """Test the truncate method."""

    def test_truncate_with_default_decimals(self, number_instance):
        truncated_number = number_instance.geetools.truncate()
        assert truncated_number.getInfo() == 1234.56

    def test_truncate_with_custom_decimals(self, number_instance):
        truncated_number = number_instance.geetools.truncate(1)
        assert truncated_number.getInfo() == 1234.5

    def test_truncate_with_zero_decimals(self, number_instance):
        truncated_number = number_instance.geetools.truncate(0)
        assert truncated_number.getInfo() == 1234.0

    def test_truncate_with_large_decimals(self, number_instance):
        truncated_number = number_instance.geetools.truncate(5)
        assert truncated_number.getInfo() == 1234.56785


class TestIsClose:
    """Test the ``isClose`` method."""

    def test_is_close(self, number_instance):
        is_close = number_instance.geetools.isClose(1234.56785678)
        assert is_close.getInfo() == 1

    def test_is_not_close(self, number_instance):
        is_close = number_instance.geetools.isClose(1234.5)
        assert is_close.getInfo() == 0

    def test_is_close_with_custom_tolerance(self, number_instance):
        is_close = number_instance.geetools.isClose(1234.5678567, 1e-5)
        assert is_close.getInfo() == 1

    def test_is_close_with_zero_tolerance(self, number_instance):
        is_close = number_instance.geetools.isClose(1234.56785678, 0)
        assert is_close.getInfo() == 1
