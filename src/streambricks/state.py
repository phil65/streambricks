from __future__ import annotations

from typing import Self, TypeVar

from pydantic import BaseModel
import streamlit as st


T = TypeVar("T", bound=BaseModel)


class State(BaseModel):
    @classmethod
    def get(cls, *, key: str | None = None) -> Self:
        """Get or initialize typed state for Streamlit.

        Args:
            model_class: Pydantic model class defining the state structure
            key: Optional key to use in session_state (defaults to model class name)

        Returns:
            An instance of the model representing current state
        """
        state_key = key or cls.__name__
        if state_key not in st.session_state:
            st.session_state[state_key] = cls()

        current_state = st.session_state[state_key]
        if not isinstance(current_state, cls):
            st.session_state[state_key] = cls()

        return st.session_state[state_key]

    @classmethod
    def set(cls, *, key: str | None = None, value: Self):
        """Set state to given model.

        Args:
            key: Optional key to use in session_state (defaults to model class name)
            value: The value to set in session_state
        """
        state_key = key or cls.__name__
        st.session_state[state_key] = value

    @classmethod
    def reset(cls, *, key: str | None = None):
        """Reset state.

        Args:
            key: Optional key to use in session_state (defaults to model class name)
        """
        state_key = key or cls.__name__
        st.session_state[state_key] = cls()
