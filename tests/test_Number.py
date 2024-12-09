"""test the Number class methods."""


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
