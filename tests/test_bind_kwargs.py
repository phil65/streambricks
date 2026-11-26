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


def test_unbound_params_may_use_type_checking_only_names() -> None:
    """Annotations of parameters that are not bound are never evaluated (PEP 649)."""
    from typing import TYPE_CHECKING

    from streambricks.widgets.bind_kwargs import bind_kwargs_as_widget

    if TYPE_CHECKING:
        from decimal import Decimal  # only imported for type checkers

    def compute(value: Decimal, factor: int = 2) -> int:
        return factor

    wrapped = bind_kwargs_as_widget(compute, kwargs_to_bind=["factor"])
    assert wrapped.__name__ == "compute"
