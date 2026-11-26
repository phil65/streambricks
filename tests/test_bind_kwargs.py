"""Tests for the Optional unwrapping used by bind_kwargs_as_widget."""

from typing import Optional, Union

import pytest

from streambricks.widgets.bind_kwargs import unwrap_optional


@pytest.mark.parametrize(
    ("tp", "expected"),
    [
        (int | None, int),
        (None | str, str),
        (Optional[float], float),  # noqa: UP045
        (Union[bytes, None], bytes),  # noqa: UP007
        (int | str | None, int | str | None),
        (int | str, int | str),
        (int, int),
        (list[int], list[int]),
    ],
)
def test_unwrap_optional(tp: object, expected: object) -> None:
    assert unwrap_optional(tp) == expected
