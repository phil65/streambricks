"""Sequence management widget for streamlit applications."""

from __future__ import annotations

from typing import Any

import streamlit as st

from streambricks.widgets.model_widget.main import get_field_renderer


def sequence_widget[T](
    label: str,
    item_type: type[T],
    value: list[T] | None = None,
    key: str | None = None,
    disabled: bool = False,
    help: str | None = None,  # noqa: A002
    **field_info: Any,
) -> list[T]:
    """Create a widget for managing sequences (lists) of items.

    Args:
        label: Label to display
        item_type: Type of items in the sequence
        value: Current sequence value
        key: Optional unique key for widget state
        disabled: Whether the widget is disabled
        help: Help text to display
        field_info: Additional field information

    Returns:
        Updated sequence of items
    """
    widget_key = key or label
    items_key = f"{widget_key}_items"
    add_item_key = f"{widget_key}_add_item"
    if items_key not in st.session_state:
        st.session_state[items_key] = list(value) if value is not None else []

    label_col, widget_col = st.columns([1, 3])
    with label_col:
        st.markdown(f"**{label}**")
        if help:
            st.caption(help)

    with widget_col:
        if st.button("Add Item", key=add_item_key, disabled=disabled):
            from streambricks.widgets.type_helpers import add_new_item

            add_new_item(st.session_state[items_key], item_type)

        items_to_delete = []
        item_info = field_info.copy()
        item_info["type"] = item_type

        try:
            renderer = get_field_renderer(item_info)
            for i, item in enumerate(st.session_state[items_key]):
                cols = st.columns([0.8, 0.2])
                with cols[0]:
                    st.session_state[items_key][i] = renderer(
                        key=f"{widget_key}_item_{i}",
                        value=item,
                        label=f"Item {i + 1}",
                        disabled=disabled,
                        **item_info,
                    )
                with cols[1]:
                    st.write("")
                    if st.button("🗑️", key=f"{widget_key}_delete_{i}", disabled=disabled):
                        items_to_delete.append(i)

            if items_to_delete:
                for idx in sorted(items_to_delete, reverse=True):
                    if 0 <= idx < len(st.session_state[items_key]):
                        st.session_state[items_key].pop(idx)
                st.rerun()

        except Exception as e:  # noqa: BLE001
            st.error(f"Error rendering sequence items: {e!s}")

    return st.session_state[items_key]


if __name__ == "__main__":
    from pydantic import BaseModel

    from streambricks.helpers import run

    class SubItem(BaseModel):
        name: str = ""
        value: int = 0

    def demo():
        st.title("Sequence Widget Demo")
        numbers = sequence_widget(
            "Numbers",
            int,
            value=[1, 2, 3],
            help="A list of integers",
        )
        st.write("Current numbers:", numbers)
        items = sequence_widget(
            "Complex Items",
            SubItem,
            value=[SubItem(name="Item 1", value=42)],
            help="A list of SubItems",
        )
        st.write("Current items:", [item.model_dump() for item in items])

    run(demo)
