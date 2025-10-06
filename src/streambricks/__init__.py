"""StreamBricks components for Streamlit."""

from __future__ import annotations

from importlib.metadata import version

__version__ = version("streambricks")

from streambricks.auth import (
    GoogleUser,
    MicrosoftUser,
    get_current_user,
    google_login,
    microsoft_login,
    profile_widget,
    requires_login,
)
from streambricks.widgets.model_widget import (
    render_model_form as model_edit,
    render_model_readonly as model_display,
)
from streambricks.widgets.multi_select import multiselect, MultiSelectItem
from streambricks.widgets.image_capture import image_capture
from streambricks.widgets.model_selector import (
    model_selector,
    model_selector as llm_model_selector,
)
from streambricks.helpers import run
from streambricks.state import State
from streambricks.widgets.bind_kwargs import bind_kwargs_as_widget
from streambricks.sidebar import hide_sidebar, set_sidebar_width

__all__ = [
    "GoogleUser",
    "MicrosoftUser",
    "MultiSelectItem",
    "State",
    "__version__",
    "bind_kwargs_as_widget",
    "get_current_user",
    "google_login",
    "hide_sidebar",
    "image_capture",
    "llm_model_selector",
    "microsoft_login",
    "model_display",
    "model_edit",
    "model_selector",
    "multiselect",
    "profile_widget",
    "requires_login",
    "run",
    "set_sidebar_width",
]
