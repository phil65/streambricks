"""Utility functions for Streamlit applications."""

from __future__ import annotations

import asyncio
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
import inspect
import sys
from typing import TYPE_CHECKING, Any, get_args

import streamlit as st
from streamlit import runtime
from streamlit.web.cli import main

from streambricks.widgets.type_helpers import is_literal_type


if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from streamlit.elements.lib.column_types import ColumnConfig


def run(fn: Callable[..., Any] | Coroutine[Any, Any, Any], *args: Any, **kwargs: Any):
    """Run a function or coroutine with Streamlit.

    If Streamlit runtime exists, execute the function directly. Otherwise,
    start Streamlit with the current script.

    Args:
        fn: The function or coroutine to run
        args: Positional arguments to pass to the function
        kwargs: Keyword arguments to pass to the function
    """
    if runtime.exists():
        if inspect.iscoroutine(fn):
            asyncio.run(fn)
        # Handle coroutine function
        elif inspect.iscoroutinefunction(fn):
            coro = fn(*args, **kwargs)
            asyncio.run(coro)
        # Handle regular function
        else:
            fn(*args, **kwargs)  # type: ignore
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(main())


def get_column_for_type(  # noqa: PLR0911
    typ: type,
    title: str,
    *,
    required: bool = True,
    help: str | None = None,  # noqa: A002
    **kwargs: Any,
) -> ColumnConfig:
    """Get appropriate column config for a given type.

    Args:
        typ: The type to create a column for
        title: Column title/label
        required: Whether the field is required
        help: Help text for the column
        **kwargs: Additional arguments passed to column constructor

    Returns:
        Configured column for the type
    """
    # Handle literal types
    if is_literal_type(typ):
        options = get_args(typ)
        return st.column_config.SelectboxColumn(
            title,
            help=help,
            required=required,
            options=options,
            **kwargs,
        )

    # Handle enums
    if isinstance(typ, type) and issubclass(typ, Enum):
        return st.column_config.SelectboxColumn(
            title,
            help=help,
            required=required,
            options=list(typ.__members__.values()),  # type: ignore
            **kwargs,
        )

    # Match on type
    match typ:
        case type() as t if t is bool:
            return st.column_config.CheckboxColumn(
                title,
                help=help,
                **kwargs,
            )

        case type() as t if t in (int, float, Decimal):
            return st.column_config.NumberColumn(
                title,
                help=help,
                required=required,
                **kwargs,
            )

        case type() as t if t is str:
            return st.column_config.TextColumn(
                title,
                help=help,
                required=required,
                **kwargs,
            )

        case type() as t if t is datetime:
            return st.column_config.DatetimeColumn(
                title,
                help=help,
                required=required,
                **kwargs,
            )

        case type() as t if t is date:
            return st.column_config.DateColumn(
                title,
                help=help,
                required=required,
                **kwargs,
            )

        case type() as t if t is time:
            return st.column_config.TimeColumn(
                title,
                help=help,
                required=required,
                **kwargs,
            )

        case _:
            # Default to generic column for unsupported types
            return st.column_config.Column(
                title,
                help=help,
                required=required,
                **kwargs,
            )
