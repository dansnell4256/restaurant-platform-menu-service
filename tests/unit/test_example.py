"""Example test to verify pytest configuration works."""

import pytest


@pytest.mark.unit
def test_example() -> None:
    """Test that basic assertions work."""
    assert 1 + 1 == 2
