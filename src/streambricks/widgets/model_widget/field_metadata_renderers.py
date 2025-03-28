"""Field metadata type renderers for Pydantic form fields."""

from __future__ import annotations

from typing import Any


def render_model_id_field(
    *,
    key: str,
    value: str | None = None,
    label: str | None = None,
    disabled: bool = False,
    help: str | None = None,  # noqa: A002
    **field_info: Any,
) -> str:
    """Render a model identifier field using model_selector widget."""
    from streambricks.widgets.model_selector import model_selector

    providers = field_info.get("providers")
    selected_model = model_selector(value=value, providers=providers, expanded=False)
    return selected_model.pydantic_ai_id if selected_model else value or ""
