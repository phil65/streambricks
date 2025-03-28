"""Primitive type renderers for Pydantic form fields."""

from __future__ import annotations

import contextlib
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, get_args

from pydantic import SecretStr
import streamlit as st


def render_str_field(
    *,
    key: str,
    value: str | None = None,
    label: str | None = None,
    disabled: bool = False,
    help: str | None = None,  # noqa: A002
    **field_info: Any,
) -> str:
    """Render a string field using appropriate Streamlit widget."""
    max_length = field_info.get("max_length", 0)
    multiple_lines = field_info.get("multiple_lines", False)
    safe_value = "" if value is None else value
    has_meaningful_content = safe_value.strip() != ""
    has_line_breaks = has_meaningful_content and (
        "\n" in safe_value or "\r" in safe_value
    )
    is_long_val = len(safe_value) > 100  # noqa: PLR2004
    use_text_area = max_length > 100 or is_long_val or multiple_lines or has_line_breaks  # noqa: PLR2004

    if use_text_area:
        return st.text_area(
            label=label or key,
            value=safe_value,
            disabled=disabled,
            key=key,
            help=help,
        )

    return st.text_input(
        label=label or key,
        value=safe_value.strip() if has_meaningful_content else safe_value,
        disabled=disabled,
        key=key,
        help=help,
    )


def render_int_field(
    *,
    key: str,
    value: int | None = None,
    label: str | None = None,
    disabled: bool = False,
    help: str | None = None,  # noqa: A002
    **field_info: Any,
) -> int:
    """Render an integer field using Streamlit number_input."""
    # Set default value
    safe_value = int(value) if value is not None else 0
    min_value = field_info.get("ge") or field_info.get("gt")
    min_value = int(min_value) if min_value is not None else None
    max_value = field_info.get("le") or field_info.get("lt")
    max_value = int(max_value) if max_value is not None else None
    step = field_info.get("multiple_of")
    step = int(step) if step is not None else 1
    result = st.number_input(
        label=label or key,
        value=safe_value,
        min_value=min_value,
        max_value=max_value,
        step=step,
        disabled=disabled,
        key=key,
        format="%d",
        help=help,
    )

    return int(result)


def render_float_field(
    *,
    key: str,
    value: float | Decimal | None = None,
    label: str | None = None,
    disabled: bool = False,
    help: str | None = None,  # noqa: A002
    **field_info: Any,
) -> float | Decimal:
    """Render a float or Decimal field using Streamlit number_input."""
    field_type = field_info.get("type")
    is_decimal = field_type is Decimal
    safe_value = float(value) if value is not None else 0.0
    min_value = field_info.get("ge") or field_info.get("gt")
    min_value = float(min_value) if min_value is not None else None
    max_value = field_info.get("le") or field_info.get("lt")
    max_value = float(max_value) if max_value is not None else None
    step = field_info.get("multiple_of")
    step = float(step) if step is not None else 0.01
    result = st.number_input(
        label=label or key,
        value=safe_value,
        min_value=min_value,
        max_value=max_value,
        step=step,
        disabled=disabled,
        key=key,
        help=help,
    )

    if is_decimal:
        return Decimal(str(result))

    return result


def render_bool_field(
    *,
    key: str,
    value: bool | None = None,
    label: str | None = None,
    disabled: bool = False,
    help: str | None = None,  # noqa: A002
    **field_info: Any,
) -> bool:
    """Render a boolean field using appropriate Streamlit widget."""
    return st.checkbox(
        label=label or key,
        value=value if value is not None else False,
        disabled=disabled,
        key=key,
        help=help,
    )


def render_date_field(
    *,
    key: str,
    value: date | None = None,
    label: str | None = None,
    disabled: bool = False,
    help: str | None = None,  # noqa: A002
    **field_info: Any,
) -> date:
    """Render a date field using appropriate Streamlit widget."""
    return st.date_input(
        label=label or key,
        value=value or date.today(),
        disabled=disabled,
        key=key,
        help=help,
    )


def render_time_field(
    *,
    key: str,
    value: time | None = None,
    label: str | None = None,
    disabled: bool = False,
    help: str | None = None,  # noqa: A002
    **field_info: Any,
) -> time:
    """Render a time field using appropriate Streamlit widget."""
    return st.time_input(
        label=label or key,
        value=value or datetime.now().time(),
        disabled=disabled,
        key=key,
        help=help,
    )


def render_enum_field(
    *,
    key: str,
    value: Enum | None = None,
    label: str | None = None,
    disabled: bool = False,
    help: str | None = None,  # noqa: A002
    **field_info: Any,
) -> Enum:
    """Render an enum field using appropriate Streamlit widget."""
    enum_class = field_info.get("enum_class") or field_info.get("type")
    if enum_class is None or not issubclass(enum_class, Enum):
        error_msg = f"Invalid enum class for field {key}"
        raise TypeError(error_msg)
    options = list(enum_class.__members__.values())
    if not options:
        return None  # type: ignore
    index = 0
    if value is not None:
        with contextlib.suppress(ValueError):
            index = options.index(value)
    return st.selectbox(
        label=label or key,
        options=options,
        index=index,
        disabled=disabled,
        key=key,
        help=help,
    )


def render_secret_str_field(
    *,
    key: str,
    value: SecretStr | None = None,
    label: str | None = None,
    disabled: bool = False,
    help: str | None = None,  # noqa: A002
    **field_info: Any,
) -> SecretStr:
    """Render a SecretStr field using a password input."""
    text = st.text_input(
        label=label or key,
        value=value.get_secret_value() if value else "",
        disabled=disabled,
        key=key,
        help=help,
        type="password",
    )
    return SecretStr(text)


def render_datetime_field(
    *,
    key: str,
    value: datetime | None = None,
    label: str | None = None,
    disabled: bool = False,
    help: str | None = None,  # noqa: A002
    **field_info: Any,
) -> datetime:
    """Render a datetime field using date and time inputs."""
    current_date = value.date() if value else date.today()
    current_time = value.time() if value else datetime.now().time()
    date_col, time_col = st.columns(2)
    with date_col:
        selected_date = st.date_input(
            label=f"{label or key} (Date)",
            value=current_date,
            disabled=disabled,
            key=f"{key}_date",
            help=help,
        )
    with time_col:
        selected_time = st.time_input(
            label=f"{label or key} (Time)",
            value=current_time,
            disabled=disabled,
            key=f"{key}_time",
            help=help,
        )

    return datetime.combine(selected_date, selected_time)


def render_literal_field(
    *,
    key: str,
    value: Any = None,
    label: str | None = None,
    disabled: bool = False,
    help: str | None = None,  # noqa: A002
    **field_info: Any,
) -> Any:
    """Render a Literal field using appropriate Streamlit widget."""
    annotation = field_info.get("type") or field_info.get("annotation")
    options = get_args(annotation)
    if len(options) == 1:
        return options[0]
    if all(isinstance(opt, bool) for opt in options):
        index = options.index(value) if value in options else 0
        return st.radio(
            label=label or key,
            options=options,
            index=index,
            disabled=disabled,
            key=key,
            horizontal=True,
            help=help,
        )

    # Use selectbox for other literals
    index = options.index(value) if value in options else 0
    return st.selectbox(
        label=label or key,
        options=options,
        index=index,
        disabled=disabled,
        key=key,
        help=help,
    )
