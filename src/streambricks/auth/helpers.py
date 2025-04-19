from __future__ import annotations

from typing import Any, TypeVar, overload

import streamlit as st

from streambricks.auth.models import GoogleUser, MicrosoftUser


T = TypeVar("T", GoogleUser, MicrosoftUser)


def _get_user_data() -> dict[str, Any] | None:
    """Get user data from either experimental_user or stable user attribute."""
    # Try stable version first
    if hasattr(st, "user") and getattr(st.user, "is_logged_in", False):  # pyright: ignore
        return {**st.user}  # pyright: ignore

    # Fall back to experimental version
    if hasattr(st, "experimental_user") and st.experimental_user.is_logged_in:
        return {**st.experimental_user}

    return None


def google_login(
    button_text: str = "Login with Google",
    redirect_url: str | None = None,
    key: str | None = None,
) -> GoogleUser | None:
    """Authenticate user with Google and return typed user object if successful.

    Args:
        button_text: Text to display on the login button
        redirect_url: URL to redirect to after successful login
        key: Streamlit widget key for the login button

    Returns:
        GoogleUser object if login successful, None otherwise
    """
    user_data = _get_user_data()
    if user_data is not None:
        # User is already logged in, return typed user object
        return GoogleUser(is_logged_in=True, **user_data)  # pyright: ignore

    # User not logged in, display login button
    if st.button(button_text, key=key):
        # The provider parameter should match what's configured in secrets.toml
        st.login("google")

    return None


def microsoft_login(
    button_text: str = "Login with Microsoft",
    redirect_url: str | None = None,
    key: str | None = None,
) -> MicrosoftUser | None:
    """Authenticate user with Microsoft and return typed user object if successful.

    Args:
        button_text: Text to display on the login button
        redirect_url: URL to redirect to after successful login
        key: Streamlit widget key for the login button

    Returns:
        MicrosoftUser object if login successful, None otherwise
    """
    user_data = _get_user_data()
    if user_data is not None:
        # User is already logged in, return typed user object
        return MicrosoftUser(is_logged_in=True, **user_data)  # pyright: ignore

    # User not logged in, display login button
    if st.button(button_text, key=key):
        # The provider parameter should match what's configured in secrets.toml
        st.login("microsoft")

    return None


@overload
def get_current_user(user_class: type[T]) -> T: ...


@overload
def get_current_user() -> GoogleUser | MicrosoftUser | None: ...


def get_current_user(
    user_class: type[T] | None = None,
) -> T | GoogleUser | MicrosoftUser | None:
    """Get the currently logged in user as a typed object.

    Args:
        user_class: The class to use for the user model (GoogleUser or MicrosoftUser).
                   If specified, errors will be raised if the data doesn't match.

    Returns:
        Typed user object if logged in and matching requested type,
        None if no user_class specified and no user is logged in

    Raises:
        Various exceptions: If the user data doesn't match the requested model,
                          the original validation exceptions from Pydantic will be raised
    """
    user_data = _get_user_data()
    if user_data is None:
        if user_class is not None:
            msg = "No user is currently logged in"
            raise ValueError(msg)
        return None

    if user_class is not None:
        return user_class(is_logged_in=True, **user_data)  # pyright: ignore
    try:
        return GoogleUser(is_logged_in=True, **user_data)  # pyright: ignore
    except Exception:  # noqa: BLE001
        try:
            return MicrosoftUser(is_logged_in=True, **user_data)  # pyright: ignore
        except Exception:  # noqa: BLE001
            return None
