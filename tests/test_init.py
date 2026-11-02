"""Tests for package initialization."""

import ee

import geetools  # noqa: F401


def test_user_agent():
    """Set the Earth Engine user agent to the geetools sentinel."""
    assert ee.data.getUserAgent() == "geetools"
