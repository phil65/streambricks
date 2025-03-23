"""Model selector component for streamlit applications."""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st


if TYPE_CHECKING:
    from collections.abc import Sequence

    from tokonomics.model_discovery import ModelInfo, ProviderType


def model_selector(
    *,
    value: str | None = None,
    providers: Sequence[ProviderType] | None = None,
    expanded: bool = True,
) -> ModelInfo | None:
    """Render a model selector with provider and model dropdowns.

    Args:
        value: Initial model name to select
        providers: List of providers to show models from
        expanded: Whether to expand the model details by default

    Returns:
        Selected model info or None if not selected
    """
    from tokonomics.model_discovery import get_all_models_sync

    models = get_all_models_sync(providers=providers)
    available_providers = sorted({model.provider for model in models})
    current_model = None
    current_provider = None
    if value:
        current_model = next(
            (m for m in models if m.pydantic_ai_id == value),
            None,
        )
        if current_model:
            current_provider = current_model.provider

    if len(available_providers) > 1:
        default_provider_idx = (
            available_providers.index(current_provider)
            if current_provider in available_providers
            else 0
        )
        selected_provider = st.selectbox(
            "Provider",
            options=available_providers,
            index=default_provider_idx,
        )
    else:
        selected_provider = available_providers[0]

    provider_models = [m for m in models if m.provider == selected_provider]
    model_names = [m.name for m in provider_models]
    default_model_idx = 0
    if current_model and current_model.provider == selected_provider:
        try:
            default_model_idx = model_names.index(current_model.name)
        except ValueError:
            default_model_idx = 0

    selected_name = st.selectbox("Model", options=model_names, index=default_model_idx)
    selected_model = next((m for m in provider_models if m.name == selected_name), None)
    if selected_model:
        with st.expander("Model Details", expanded=expanded):
            st.markdown(selected_model.format())
    return selected_model


if __name__ == "__main__":
    from streambricks.helpers import run

    run(model_selector)
