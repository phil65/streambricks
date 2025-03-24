from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass
class MultiSelectItem[T]:
    """Represents an item in a multiselect with associated data."""

    label: str
    value: T
    description: str | None = None

    def __str__(self) -> str:
        """Return string representation for display in multiselect."""
        return self.label


def multiselect[T](
    label: str,
    items: list[MultiSelectItem[T]],
    *,
    state_key: str,
    help_text: str | None = None,
    default_all: bool = False,
) -> list[MultiSelectItem[T]]:
    """Create a multiselect widget.

    Args:
        label: The label for the multiselect
        items: List of items to select from
        state_key: Key for storing in session state
        help_text: Optional help text to display
        default_all: Whether to select all items by default

    Returns:
        List of selected MultiSelectItem objects
    """
    full_key = f"multiselect_{state_key}"
    item_map = {str(item): item for item in items}
    # Initialize state if needed
    if full_key not in st.session_state:
        default_selection = list(item_map.keys()) if default_all else []
        st.session_state[full_key] = default_selection

    # Handle case where items list changes
    valid_labels = set(item_map.keys())
    st.session_state[full_key] = [
        label for label in st.session_state[full_key] if label in valid_labels
    ]

    # Render multiselect and update state
    selected_labels = st.multiselect(
        label=label,
        options=list(item_map.keys()),
        default=st.session_state[full_key],
        help=help_text,
        key=f"{full_key}_widget",
    )

    st.session_state[full_key] = selected_labels
    return [item_map[label] for label in selected_labels]


if __name__ == "__main__":
    import streamlit as st

    items = [
        MultiSelectItem("Apple", "🍎"),
        MultiSelectItem("Banana", "🍌"),
        MultiSelectItem("Cherry", "🍒"),
    ]

    selected_items = multiselect(
        label="Fruits",
        items=items,
        state_key="fruits",
        help_text="Select your favorite fruits",
        default_all=True,
    )

    st.write("Selected fruits:", selected_items)
