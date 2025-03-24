from __future__ import annotations

from typing import TypeVar, cast

from pydantic import BaseModel
import streamlit as st


T = TypeVar("T", bound=BaseModel)


def get_state(model_class: type[T], *, key: str | None = None) -> T:
    """Get or initialize typed state for Streamlit.

    Args:
        model_class: Pydantic model class defining the state structure
        key: Optional key to use in session_state (defaults to model class name)

    Returns:
        An instance of the model representing current state
    """
    state_key = key or model_class.__name__

    # Initialize state if it doesn't exist
    if state_key not in st.session_state:
        st.session_state[state_key] = model_class()

    # Ensure state is the correct type
    current_state = st.session_state[state_key]
    if not isinstance(current_state, model_class):
        st.session_state[state_key] = model_class()

    return cast(T, st.session_state[state_key])
