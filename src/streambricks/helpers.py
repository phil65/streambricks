"""Utility functions for Streamlit applications."""

from __future__ import annotations

import asyncio
import inspect
import sys
from typing import TYPE_CHECKING, Any, TypeVar

from streamlit import runtime
from streamlit.web.cli import main


if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine


T = TypeVar("T")


def run(
    fn: Callable[..., T | Coroutine[Any, Any, T]] | Coroutine[Any, Any, T],
    *args: Any,
    **kwargs: Any,
) -> None:
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
