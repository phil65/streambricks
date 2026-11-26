"""Smoke test: the package imports and reports its version."""

import streambricks


def test_package_imports() -> None:
    """The package can be imported and exposes a version string."""
    assert isinstance(streambricks.__version__, str)
