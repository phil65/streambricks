from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

import streamlit as st


if TYPE_CHECKING:
    from collections.abc import Callable


T = TypeVar("T")
P = ParamSpec("P")


def requires_login(
    func: Callable[P, T] | None = None,
    *,
    unauthorized_handler: str | Callable[[], Any] | None = None,
) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator that requires a user to be logged in via Streamlit.

    Args:
        func: The function to wrap. If None, returns a decorator.
        unauthorized_handler: How to handle unauthorized access:
            - If None: Shows default error message
            - If str: Shows that string as an error message
            - If Callable: Calls the function for custom handling

    Returns:
        Decorated function that checks login status before executing.

    Examples:
        @requires_login
        def protected_page():
            st.write("Protected content")

        @requires_login(unauthorized_handler="Please log in first")
        def dashboard():
            st.write("Dashboard content")

        @requires_login(unauthorized_handler=lambda: st.switch_page("pages/login.py"))
        def analytics():
            st.write("Analytics")
    """

    def default_unauthorized_handler() -> None:
        st.error("You need to be logged in to access this page")
        st.button("Log in with Google", on_click=st.login)

    def get_handler() -> Callable[[], Any]:
        if unauthorized_handler is None:
            return default_unauthorized_handler
        if isinstance(unauthorized_handler, str):
            return lambda: st.error(unauthorized_handler)
        return unauthorized_handler

    def decorator(fn: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if hasattr(st, "experimental_user") and st.experimental_user.is_logged_in:
                return fn(*args, **kwargs)

            # Handle unauthorized access
            handler = get_handler()
            handler()

            # Return early with None
            return None  # type: ignore

        return wrapper

    # Handle both @requires_login and @requires_login()
    if func is None:
        return decorator

    return decorator(func)
