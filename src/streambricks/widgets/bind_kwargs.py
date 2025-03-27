"""Widget binder that exposes function kwargs as configurable widgets."""

from __future__ import annotations

from functools import wraps
from inspect import Parameter, signature
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

from pydantic import Field, create_model
import streamlit as st

from streambricks.widgets.model_widget import render_model_form


if TYPE_CHECKING:
    from collections.abc import Callable


T = TypeVar("T")
P = ParamSpec("P")


def bind_kwargs_as_widget(
    func: Callable[P, T],
    *,
    kwargs_to_bind: list[str],
    widget_prefix: str = "",
    title: str | None = None,
) -> Callable[P, T]:
    """Bind function kwargs as Streamlit widgets.

    Creates a new function that wraps the original, displaying configurable
    widgets for the specified kwargs before executing the original function.

    Args:
        func: The function whose kwargs should be exposed as widgets
        kwargs_to_bind: List of kwarg names to expose as widgets
        widget_prefix: Prefix for widget keys to avoid conflicts
        title: Optional title to display above the widgets

    Returns:
        A new function that wraps the original with widget-configurable kwargs
    """
    # Get function signature
    sig = signature(func)

    # Create a dynamic model for the kwargs we want to expose
    fields = {}
    defaults = {}
    docstrings = {}

    # Extract parameter annotations and docstrings from function
    func_doc = func.__doc__ or ""
    param_docs = {}

    # Very simple docstring parser for param descriptions
    if func_doc:
        lines = func_doc.split("\n")
        in_params = False
        current_param = None

        for line in lines:
            line = line.strip()

            # Check for param section markers
            if line.lower() in ("parameters:", "args:", "arguments:"):
                in_params = True
                continue

            if in_params and line and line[0] == ":":
                # Handle :param name: description format
                if line.startswith(":param "):
                    parts = line[7:].split(":", 1)
                    if len(parts) == 2:  # noqa: PLR2004
                        param_name = parts[0].strip()
                        param_docs[param_name] = parts[1].strip()
                        current_param = param_name
                # Handle :return: which ends the params section
                elif line.startswith(":return"):
                    in_params = False
                # Handle continued description on next line
                elif current_param:
                    param_docs[current_param] += " " + line
            elif in_params and line and line[0] != ":":
                # Standard format: param_name: description
                if ":" in line:
                    parts = line.split(":", 1)
                    param_name = parts[0].strip()
                    param_docs[param_name] = parts[1].strip()
                    current_param = param_name
                # Handle continued description on next line
                elif current_param:
                    param_docs[current_param] += " " + line

    # Extract field types and defaults from function signature
    for name, param in sig.parameters.items():
        if name in kwargs_to_bind:
            param_type = param.annotation if param.annotation != Parameter.empty else Any
            default = param.default if param.default != Parameter.empty else None

            # Handle special case: Optional types
            if param_type.__class__.__name__ == "_UnionGenericAlias":  # pyright: ignore
                # For Union[X, None] types (Optional[X])
                args = getattr(param_type, "__args__", ())
                if len(args) == 2 and args[1] is type(None):  # noqa: PLR2004
                    param_type = args[0]

            # Create field with appropriate defaults and metadata
            field_kwargs = {"default": default}

            # Add description from docstring if available
            if name in param_docs:
                field_kwargs["description"] = param_docs[name]
                docstrings[name] = param_docs[name]

            fields[name] = (param_type, Field(**field_kwargs))  # pyright: ignore
            if default != Parameter.empty:
                defaults[name] = default

    # Create a Pydantic model dynamically
    model_name = f"{func.__name__}Config"
    config_model = create_model(model_name, **fields)

    # Add docstrings as class variables
    for name, docstring in docstrings.items():
        setattr(config_model, f"__doc_{name}__", docstring)

    # Create a session state key for storing current config
    config_key = f"{widget_prefix}_{func.__name__}_config"

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        # Initialize config in session state if needed
        if config_key not in st.session_state:
            # Initialize with defaults
            config_data = {
                name: (defaults.get(name))
                for name in kwargs_to_bind
                if name in sig.parameters
            }
            # Override with any provided values in kwargs
            for name in kwargs_to_bind:
                if name in kwargs:
                    config_data[name] = kwargs[name]

            st.session_state[config_key] = config_model(**config_data)

        # Display title if provided
        if title:
            st.subheader(title)

        # Render config form
        updated_config = render_model_form(st.session_state[config_key])
        st.session_state[config_key] = updated_config

        # Update kwargs with values from the form
        for name in kwargs_to_bind:
            if hasattr(updated_config, name):
                kwargs[name] = getattr(updated_config, name)

        # Call the original function
        return func(*args, **kwargs)

    return wrapper


if __name__ == "__main__":
    from typing import Any, Literal

    import streamlit as st

    from streambricks.helpers import run

    def complex_function(
        a: int,
        b: str,
        show_details: bool = False,
        format_type: Literal["simple", "detailed", "compact"] = "simple",
        max_items: int = 5,
        threshold: float = 0.75,
    ) -> None:
        """Function with various kwargs that can be configured via widgets.

        Args:
            a: First parameter value
            b: Second parameter string
            show_details: Whether to show additional details
            format_type: The format to use for display
            max_items: Maximum number of items to show
            threshold: Threshold value for filtering
        """
        st.write(f"Regular args: a={a}, b={b}")
        st.write(f"Format type: {format_type}")

        if show_details:
            st.write("Details enabled!")
            st.write(f"Threshold: {threshold}")

        st.write(f"Showing {max_items} items:")
        for i in range(max_items):
            st.write(f"Item {i + 1}")

    # Bind specific kwargs to widgets
    configurable_function = bind_kwargs_as_widget(
        complex_function,
        kwargs_to_bind=["show_details", "format_type", "max_items", "threshold"],
        title="Configure Function",
    )

    def demo():
        st.title("Bind Args as Widget Demo")

        # Regular inputs for non-widget args
        a = st.number_input("Value for a", value=10)
        b = st.text_input("Value for b", value="hello")

        # This will display widgets for the bound kwargs
        # and then call the function with those values
        configurable_function(a, b)

    run(demo)
