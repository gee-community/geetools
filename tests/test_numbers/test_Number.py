"""test the Number class methods"""
import ee
import pytest

import geetools

class TestTruncate:
    """Test the truncate method"""

    def test_truncate_with_default_decimals(self, my_number_instance):
        truncated_number = my_number_instance.geetools.truncate()
        assert truncated_number.getInfo() == 1234.57

    def test_truncate_with_custom_decimals(self, my_number_instance):
        truncated_number = my_number_instance.geetools.truncate(1)
        assert truncated_number.getInfo() == 1234.5

    def test_truncate_with_zero_decimals(self, my_number_instance):
        truncated_number = my_number_instance.geetools.truncate(0)
        assert truncated_number.getInfo() == 1234.0

    def test_truncate_with_large_decimals(self, my_number_instance):
        truncated_number = my_number_instance.geetools.truncate(5)
        assert truncated_number.getInfo() == 1234.5678

    def test_deprecated_method(self, my_number_instance):
        with pytest.deprecated_call():
            truncated_number = geetools.tools.trimDecimals(my_number_instance , 2)
            assert truncated_number.getInfo() == 1234.57

    @pytest.fixture
    def my_number_instance(self):
        """return a defined number instance"""
        return ee.Number(1234.56785678)