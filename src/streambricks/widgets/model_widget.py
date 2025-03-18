"""Primitive type handlers for Pydantic form fields."""

from __future__ import annotations

from collections.abc import Callable, Sequence
import contextlib
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal, TypeVar, get_args, get_origin, overload

import fieldz
import streamlit as st


if TYPE_CHECKING:
    from pydantic import BaseModel

T = TypeVar("T")
WidgetFunc = Callable[..., T]


def _get_with_default(obj: Any, field_name: str, field_info: Any = None) -> Any:  # noqa: PLR0911
    """Get field value with appropriate default if it's missing."""
    # Get the raw value
    value = getattr(obj, field_name, None)

    # If value isn't MISSING, return it as is
    if value != "MISSING":
        return value

    # If we don't have field info, get it
    if field_info is None:
        for field in fieldz.fields(obj.__class__):
            if field.name == field_name:
                field_info = field
                break

    # If we have field info, use it to determine appropriate default
    if field_info is not None:
        field_type = field_info.type

        # Handle Union types
        if is_union_type(field_type):
            types = [t for t in get_args(field_type) if t is not type(None)]
            if int in types:
                return 0
            if float in types:
                return 0.0
            if str in types:
                return ""
            if bool in types:
                return False
            if types and isinstance(types[0], type):
                if issubclass(types[0], int):
                    return 0
                if issubclass(types[0], float):
                    return 0.0
                if issubclass(types[0], str):
                    return ""
                if issubclass(types[0], bool):
                    return False

        # Handle basic types
        if isinstance(field_type, type):
            if issubclass(field_type, int):
                return 0
            if issubclass(field_type, float):
                return 0.0
            if issubclass(field_type, str):
                return ""
            if issubclass(field_type, bool):
                return False
            if (
                issubclass(field_type, list)
                or issubclass(field_type, set)
                or issubclass(field_type, tuple)
            ):
                return []

    # Default fallback for unknown types
    return None


def render_str_field(
    *,
    key: str,
    value: str | None = None,
    label: str | None = None,
    disabled: bool = False,
    **field_info: Any,
) -> str:
    """Render a string field using appropriate Streamlit widget."""
    max_length = field_info.get("max_length", 0)
    multiple_lines = field_info.get("multiple_lines", False)

    if max_length > 100 or multiple_lines:  # noqa: PLR2004
        return st.text_area(
            label=label or key,
            value=value or "",
            disabled=disabled,
            key=key,
        )

    return st.text_input(
        label=label or key,
        value=value or "",
        disabled=disabled,
        key=key,
    )


def render_int_field(
    *,
    key: str,
    value: int | None = None,
    label: str | None = None,
    disabled: bool = False,
    **field_info: Any,
) -> int:
    """Render an integer field using Streamlit number_input."""
    # Set default value
    safe_value = int(value) if value is not None else 0

    # Extract constraints, ensuring they're integers
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
        format="%d",  # Use integer format
    )

    return int(result)


def render_float_field(
    *,
    key: str,
    value: float | Decimal | None = None,
    label: str | None = None,
    disabled: bool = False,
    **field_info: Any,
) -> float | Decimal:
    """Render a float or Decimal field using Streamlit number_input."""
    # Determine if we're dealing with a Decimal
    field_type = field_info.get("type")
    is_decimal = field_type is Decimal

    # Convert to float for Streamlit compatibility
    safe_value = float(value) if value is not None else 0.0

    # Extract constraints, ensuring they're floats
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
    )

    # Convert back to Decimal if needed
    if is_decimal:
        return Decimal(str(result))

    return result


def render_bool_field(
    *,
    key: str,
    value: bool | None = None,
    label: str | None = None,
    disabled: bool = False,
    **field_info: Any,
) -> bool:
    """Render a boolean field using appropriate Streamlit widget."""
    return st.checkbox(
        label=label or key,
        value=value if value is not None else False,
        disabled=disabled,
        key=key,
    )


def render_date_field(
    *,
    key: str,
    value: date | None = None,
    label: str | None = None,
    disabled: bool = False,
    **field_info: Any,
) -> date:
    """Render a date field using appropriate Streamlit widget."""
    return st.date_input(
        label=label or key,
        value=value or date.today(),
        disabled=disabled,
        key=key,
    )


def render_time_field(
    *,
    key: str,
    value: time | None = None,
    label: str | None = None,
    disabled: bool = False,
    **field_info: Any,
) -> time:
    """Render a time field using appropriate Streamlit widget."""
    return st.time_input(
        label=label or key,
        value=value or datetime.now().time(),
        disabled=disabled,
        key=key,
    )


def render_enum_field(
    *,
    key: str,
    value: Enum | None = None,
    label: str | None = None,
    disabled: bool = False,
    **field_info: Any,
) -> Enum:
    """Render an enum field using appropriate Streamlit widget."""
    enum_class = field_info.get("enum_class") or field_info.get("type")

    # Handle the case where enum_class might not be valid
    if enum_class is None or not issubclass(enum_class, Enum):
        error_msg = f"Invalid enum class for field {key}"
        raise TypeError(error_msg)

    # Get enum options - every Enum class is iterable over its members
    options = list(enum_class.__members__.values())

    if not options:
        return None  # type: ignore

    # Find index of current value in options
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
    )


def render_literal_field(
    *,
    key: str,
    value: Any = None,
    label: str | None = None,
    disabled: bool = False,
    **field_info: Any,
) -> Any:
    """Render a Literal field using appropriate Streamlit widget."""
    annotation = field_info.get("type") or field_info.get("annotation")
    options = get_args(annotation)

    # No need for radio if only one option
    if len(options) == 1:
        return options[0]

    # Use radio for boolean literals
    if all(isinstance(opt, bool) for opt in options):
        index = options.index(value) if value in options else 0
        return st.radio(
            label=label or key,
            options=options,
            index=index,
            disabled=disabled,
            key=key,
            horizontal=True,
        )

    # Use selectbox for other literals
    index = options.index(value) if value in options else 0
    return st.selectbox(
        label=label or key,
        options=options,
        index=index,
        disabled=disabled,
        key=key,
    )


def is_literal_type(annotation: Any) -> bool:
    """Check if a type annotation is a Literal type."""
    # Check directly against the origin or special attribute
    return (
        get_origin(annotation) is Literal
        or getattr(annotation, "__origin__", None) is Literal
    )


def is_union_type(annotation: Any) -> bool:
    """Check if a type annotation is a Union type."""
    origin = get_origin(annotation)
    # Check if it's Union or Optional (which is Union[T, None])
    return origin is not None and (
        origin.__name__ == "Union" if hasattr(origin, "__name__") else False
    )


def is_sequence_type(annotation: Any) -> bool:
    """Check if a type annotation is a sequence type."""
    origin = get_origin(annotation)
    if origin is None:
        return False

    try:
        return issubclass(origin, list | set | tuple)
    except TypeError:
        # Handle case where origin is not a class
        return False


def render_union_field(  # noqa: PLR0911
    *,
    key: str,
    value: Any = None,
    label: str | None = None,
    disabled: bool = False,
    **field_info: Any,
) -> Any:
    """Render a field that can accept multiple types."""
    annotation = field_info.get("type") or field_info.get("annotation")
    possible_types = get_args(annotation)

    # Create type selector
    type_key = f"{key}_type"
    type_names = [
        t.__name__ if hasattr(t, "__name__") else str(t) for t in possible_types
    ]

    selected_type_name = st.selectbox(
        f"Type for {label or key}",
        options=type_names,
        key=type_key,
        disabled=disabled,
    )

    # Find selected type
    selected_type_index = type_names.index(selected_type_name)
    selected_type = possible_types[selected_type_index]

    # Create field for selected type
    field_key = f"{key}_value"
    modified_field_info = field_info.copy()
    modified_field_info["type"] = selected_type

    # Only pass value if it matches the selected type or can be converted
    typed_value: Any = None
    if value is not None:
        # Try to convert the value to the selected type
        try:
            if selected_type is int and isinstance(value, int | float):
                typed_value = int(value)
            elif selected_type is float and isinstance(value, int | float):
                typed_value = float(value)
            elif selected_type is str:
                typed_value = str(value)
            elif selected_type is bool:
                # Handle conversion to bool (0/False, anything else/True)
                if isinstance(value, int | float):
                    typed_value = bool(value)
                else:
                    typed_value = bool(value)
            elif isinstance(value, selected_type):
                typed_value = value
        except (ValueError, TypeError):
            # If conversion fails, start with a blank/default value
            pass

    renderer = get_field_renderer(modified_field_info)
    result = renderer(
        key=field_key,
        value=typed_value,
        label=label,
        disabled=disabled,
        **modified_field_info,
    )

    # Ensure the result is of the correct type
    try:
        if selected_type is int and not isinstance(result, int):
            return int(result)
        if selected_type is float and not isinstance(result, float):
            return float(result)
        if selected_type is str and not isinstance(result, str):
            return str(result)
        if selected_type is bool and not isinstance(result, bool):
            return bool(result)
    except (ValueError, TypeError) as e:
        error_msg = f"Cannot convert {result} to {selected_type.__name__}: {e!s}"
        st.error(error_msg)
        # Return a default value for the selected type
        if selected_type is int:
            return 0
        if selected_type is float:
            return 0.0
        if selected_type is str:
            return ""
        if selected_type is bool:
            return False
        return None
    else:
        return result


def create_default_instance(model_class: type) -> Any:
    """Create a default instance of a model with default values for required fields."""
    # Create an empty dict to collect required values
    default_values = {}

    # Get all fields
    for field in fieldz.fields(model_class):
        field_name = field.name

        # Check if the field already has a default value
        has_default = False
        if hasattr(field, "default") and field.default != "MISSING":
            # Use the field's default value
            default_values[field_name] = field.default
            has_default = True
        elif hasattr(field, "default_factory") and field.default_factory != "MISSING":
            try:
                # Use the field's default factory
                default_values[field_name] = field.default_factory()  # pyright: ignore
                has_default = True
            except Exception:  # noqa: BLE001
                # If default_factory fails, fall back to type-based defaults
                pass

        # If the field doesn't have a default, create one based on type
        if not has_default:
            field_type = field.type

            # Handle union types
            if is_union_type(field_type):
                types = [t for t in get_args(field_type) if t is not type(None)]
                if int in types:
                    default_values[field_name] = 0
                elif float in types:
                    default_values[field_name] = 0.0
                elif str in types:
                    default_values[field_name] = ""
                elif bool in types:
                    default_values[field_name] = False
                continue

            # Set type-appropriate default values based on Python type
            if isinstance(field_type, type):
                if issubclass(field_type, str):
                    default_values[field_name] = ""
                elif issubclass(field_type, int):
                    default_values[field_name] = 0
                elif issubclass(field_type, float):
                    default_values[field_name] = 0.0
                elif issubclass(field_type, bool):
                    default_values[field_name] = False
                elif is_dataclass_like(field_type):
                    # For nested models, recursively create default instances
                    default_values[field_name] = create_default_instance(field_type)

    # Create and return the instance with the default values
    try:
        return model_class(**default_values)
    except Exception as e:  # noqa: BLE001
        error_msg = f"Error creating default instance: {e}"
        st.error(error_msg)
        return None


def render_sequence_field(
    *,
    key: str,
    value: Sequence[Any] | None = None,
    label: str | None = None,
    disabled: bool = False,
    **field_info: Any,
) -> list[Any]:
    """Render a field for sequence types (list, tuple, set)."""
    annotation = field_info.get("type") or field_info.get("annotation")

    # Create unique state keys for this field
    add_item_key = f"{key}_add_item"
    items_key = f"{key}_items"

    # Initialize session state for this field
    if items_key not in st.session_state:
        st.session_state[items_key] = list(value) if value is not None else []

    # Extract item type from sequence annotation
    try:
        item_type = get_args(annotation)[0]  # Get type of sequence items
    except (IndexError, TypeError):
        item_type = Any

    # Check if we're already inside an expander
    inside_expander = field_info.get("inside_expander", False)

    # Create container for sequence elements
    if not inside_expander:
        st.markdown(f"**{label or key}**")
        with st.container():
            # Add new item button
            if st.button("Add Item", key=add_item_key, disabled=disabled):
                add_new_item(st.session_state[items_key], item_type)

            # Render items
            render_sequence_items(
                st.session_state[items_key],
                item_type,
                key,
                items_key,
                disabled,
                field_info,
            )
    else:
        # Already inside an expander, use simple container
        # Add new item button
        if st.button("Add Item", key=add_item_key, disabled=disabled):
            add_new_item(st.session_state[items_key], item_type)

        # Render items
        render_sequence_items(
            st.session_state[items_key], item_type, key, items_key, disabled, field_info
        )

    # Return the current items
    return st.session_state[items_key]


def add_new_item(items_list: list, item_type: Any) -> None:
    """Add a new item to a list based on its type."""
    if is_dataclass_like(item_type):
        # For dataclass-like types, create a default instance
        new_item = create_default_instance(item_type)
        if new_item is not None:
            items_list.append(new_item)
    # For basic types, add appropriate default values
    elif item_type is str:
        items_list.append("")
    elif item_type is int:
        items_list.append(0)
    elif item_type is float:
        items_list.append(0.0)
    elif item_type is bool:
        items_list.append(False)
    elif is_union_type(item_type):
        # For union types, use the first non-None type
        types = [t for t in get_args(item_type) if t is not type(None)]
        if int in types:
            items_list.append(0)
        elif float in types:
            items_list.append(0.0)
        elif str in types:
            items_list.append("")
        elif bool in types:
            items_list.append(False)
        else:
            items_list.append(None)
    else:
        # For unknown types, add None
        items_list.append(None)


def render_sequence_items(
    items: list,
    item_type: Any,
    key: str,
    items_key: str,
    disabled: bool,
    field_info: dict,
) -> None:
    """Render items in a sequence with delete buttons."""
    # Prepare item field info
    item_info = field_info.copy()
    item_info["type"] = item_type
    item_info["inside_expander"] = True  # Mark as inside a container

    # Try to get renderer for item type
    try:
        renderer = get_field_renderer(item_info)

        # Track which items to delete
        items_to_delete = []

        # Render each item with a delete button
        for i, item in enumerate(items):
            st.divider()
            st.markdown(f"**Item {i + 1}**")

            # Render the item
            items[i] = renderer(
                key=f"{key}_item_{i}",
                value=item,
                label=f"Item {i + 1}",
                disabled=disabled,
                **item_info,
            )

            # Delete button for this item
            delete_key = f"{key}_delete_{i}"
            if st.button("Delete Item", key=delete_key, disabled=disabled):
                items_to_delete.append(i)

        # Process deletions (in reverse order to avoid index shifting)
        if items_to_delete:
            for idx in sorted(items_to_delete, reverse=True):
                if 0 <= idx < len(items):
                    items.pop(idx)
            st.rerun()  # Force rerun after deletion

    except Exception as e:  # noqa: BLE001
        st.error(f"Error rendering sequence items: {e!s}")


def render_model_instance_field(
    *,
    key: str,
    value: Any = None,
    label: str | None = None,
    disabled: bool = False,
    **field_info: Any,
) -> Any:
    """Render a nested model instance field."""
    model_class = field_info.get("type")
    if model_class is None:
        error_msg = f"Model class not provided for field {key}"
        raise ValueError(error_msg)

    # Initialize value if none
    if value is None:
        value = create_default_instance(model_class)
        if value is None:  # If creation failed
            try:
                value = model_class()
            except Exception as e:  # noqa: BLE001
                error_msg = f"Failed to create instance of {model_class.__name__}: {e!s}"
                st.error(error_msg)
                return None

    # Check if we're already inside an expander
    inside_expander = field_info.get("inside_expander", False)

    # If needed, wrap in a container (not an expander)
    if not inside_expander:
        st.markdown(f"**{label or key}**")
        container = st.container()
        container.divider()
    else:
        container = st  # type: ignore

    # Render each field of the nested model
    updated_value = {}

    try:
        for field in fieldz.fields(model_class):
            field_name = field.name

            # Get field value and handle 'MISSING' with type-appropriate defaults
            field_value = _get_with_default(value, field_name, field)

            # Add label for the field
            container.caption(f"{field_name.replace('_', ' ').title()}")

            # Get field description if available
            if hasattr(field, "metadata") and "description" in field.metadata:
                description = field.metadata["description"]
                container.markdown(
                    f"<small>{description}</small>", unsafe_allow_html=True
                )
            elif hasattr(field, "native_field") and hasattr(
                field.native_field, "description"
            ):
                description = field.native_field.description  # type: ignore
                container.markdown(
                    f"<small>{description}</small>", unsafe_allow_html=True
                )

            # Extract field info
            nested_field_info = {
                "name": field_name,
                "type": field.type,
                "inside_expander": True,  # Mark as inside a container
            }

            # Extract additional properties
            if hasattr(field, "native_field") and hasattr(
                field.native_field, "json_schema_extra"
            ):
                nested_field_info.update(field.native_field.json_schema_extra or {})  # type: ignore

            # Render the field
            renderer = get_field_renderer(nested_field_info)
            updated_value[field_name] = renderer(
                key=f"{key}_{field_name}",
                value=field_value,
                label=field_name.replace("_", " ").title(),
                disabled=disabled,
                **nested_field_info,
            )

        # Add a divider if we're in a container
        if not inside_expander:
            container.divider()

        # Create a new instance with the updated values
        return fieldz.replace(value, **updated_value)
    except Exception as e:  # noqa: BLE001
        st.error(f"Error rendering nested model fields: {e!s}")
        return value


def is_dataclass_like(annotation: Any) -> bool:
    """Check if a type is a dataclass-like object (Pydantic model, attrs, etc.)."""
    # Check if it's a class
    if not isinstance(annotation, type):
        return False

    # Check if it's a Pydantic model (v2)
    if hasattr(annotation, "model_fields"):
        return True

    try:
        # Check if fieldz can extract fields from it
        fields = fieldz.fields(annotation)
        # If we get fields, it's a dataclass-like object
        return len(fields) > 0
    except Exception:  # noqa: BLE001
        # If fieldz can't handle it, it's not a dataclass-like object
        return False


# Mapping of Python types to render functions
PRIMITIVE_RENDERERS = {
    str: render_str_field,
    int: render_int_field,
    float: render_float_field,
    Decimal: render_float_field,
    bool: render_bool_field,
    date: render_date_field,
    time: render_time_field,
    Enum: render_enum_field,
    Literal: render_literal_field,
}


def get_field_renderer(field_info: dict[str, Any]) -> WidgetFunc[Any]:  # noqa: PLR0911
    """Get the appropriate renderer for a field based on its type and constraints."""
    annotation = field_info.get("type") or field_info.get("annotation")

    # Check for Literal first (using our helper function)
    if is_literal_type(annotation):
        return render_literal_field

    # Check for Union types
    if is_union_type(annotation):
        return render_union_field

    # Check for sequence types
    if is_sequence_type(annotation):
        return render_sequence_field

    # Get basic type (handling Optional/Union)
    origin = get_origin(annotation)
    if origin is not None:
        args = get_args(annotation)
        if len(args) > 0:
            annotation = args[0]

    # Check if it's a dataclass-like object (including Pydantic models)
    if is_dataclass_like(annotation):
        return render_model_instance_field

    # Handle Enum types - check explicitly before using issubclass
    if isinstance(annotation, type):
        try:
            if issubclass(annotation, Enum):
                field_info["enum_class"] = annotation
                return render_enum_field
        except TypeError:
            # Skip if we get a TypeError (for special typing constructs)
            pass

    # Get renderer for basic types - safely check with try/except
    for base_type, renderer in PRIMITIVE_RENDERERS.items():
        if isinstance(annotation, type):
            try:
                if issubclass(annotation, base_type):  # type: ignore
                    return renderer  # type: ignore
            except TypeError:
                # Skip if we get a TypeError (for special typing constructs)
                continue

    # Special case for Literal (fallback)
    if getattr(annotation, "__origin__", None) is Literal:
        return render_literal_field

    error_msg = f"No renderer found for type: {annotation}"
    raise ValueError(error_msg)


def render_model_readonly(model_class, instance):
    """Render a model in read-only mode using a clean label-based layout."""
    if instance is None:
        st.info("No data available")
        return

    # Create a container for the model display
    with st.container():
        # Get all fields from the model
        for field in fieldz.fields(model_class):
            field_name = field.name
            field_value = getattr(instance, field_name, None)

            # Get field metadata
            field_type = field.type
            label = field_name.replace("_", " ").title()

            # Get description if available
            description = None
            if hasattr(field, "metadata") and "description" in field.metadata:
                description = field.metadata["description"]
            elif hasattr(field, "native_field") and hasattr(
                field.native_field, "description"
            ):
                description = field.native_field.description  # type: ignore

            # Display field
            render_field_readonly(
                label=label,
                value=field_value,
                field_type=field_type,
                description=description,
                key=f"ro_{field_name}",
            )


def render_field_readonly(label, value, field_type, description=None, key=None):
    """Render a single field in read-only mode."""
    # Create a container with two columns: label and value
    cols = st.columns([0.3, 0.7])

    with cols[0]:
        st.markdown(f"**{label}:**")
        if description:
            st.caption(description)

    with cols[1]:
        display_value_readonly(value, field_type, key)


def display_value_readonly(value, field_type, key=None):
    """Display a value in read-only mode based on its type."""
    # Handle None values
    if value is None:
        st.text("—")  # Em dash to indicate empty value
        return

    # Handle collections (lists, sets, etc.)
    if is_sequence_type(field_type):
        display_sequence_readonly(value, field_type, key)
        return

    # Handle nested models
    if is_dataclass_like(field_type):
        display_model_readonly(value, key)
        return

    # Handle Enum values
    if isinstance(value, Enum):
        st.text(str(value.name))
        return

    # Handle basic types
    if isinstance(value, bool):
        st.checkbox("", value=value, disabled=True, key=key)
    elif isinstance(value, int | float | Decimal | date | time | datetime):
        st.text(str(value))
    elif isinstance(value, str):
        if len(value) > 100:  # Long text  # noqa: PLR2004
            st.text_area("", value=value, disabled=True, height=100, key=key)
        else:
            st.text(value)
    else:
        # Default fallback for other types
        st.text(str(value))


def display_sequence_readonly(value, field_type, key=None):
    """Display a sequence (list, set, tuple) in read-only mode."""
    if not value:  # Empty sequence
        st.text("No items")
        return

    # Get item type
    item_type = Any
    with contextlib.suppress(IndexError, TypeError):
        item_type = get_args(field_type)[0]

    # Display each item
    for i, item in enumerate(value):
        with st.expander(f"Item {i + 1}", expanded=False):
            display_value_readonly(item, item_type, key=f"{key}_{i}" if key else None)


def display_model_readonly(value, key=None):
    """Display a nested model in read-only mode."""
    # Get model class
    model_class = value.__class__

    # Get all fields
    for field in fieldz.fields(model_class):
        field_name = field.name
        field_value = getattr(value, field_name, None)

        # Handle 'MISSING' values
        if field_value == "MISSING":
            field_value = _get_with_default(value, field_name, field)

        # Create a sub-container for this field
        sub_key = f"{key}_{field_name}" if key else field_name

        cols = st.columns([0.3, 0.7])
        with cols[0]:
            st.markdown(f"**{field_name.replace('_', ' ').title()}:**")
        with cols[1]:
            display_value_readonly(field_value, field.type, key=sub_key)


def render_model_field(model_class, field_name, value=None):
    """Render a field from a model using fieldz to extract field information."""
    field = next((f for f in fieldz.fields(model_class) if f.name == field_name), None)

    if field is None:
        error_msg = f"Field {field_name} not found in {model_class.__name__}"
        raise ValueError(error_msg)

    # Extract field information using fieldz
    field_info = {
        "name": field.name,
        "type": field.type,
        "default": field.default,
    }

    # Extract additional properties from field metadata
    if hasattr(field, "native_field") and hasattr(
        field.native_field, "json_schema_extra"
    ):
        field_info.update(field.native_field.json_schema_extra or {})  # type: ignore

    # Get description for the label
    label = field_name.replace("_", " ").title()
    if hasattr(field, "metadata") and "description" in field.metadata:
        description = field.metadata["description"]
        field_info["description"] = description
    elif hasattr(field, "native_field") and hasattr(field.native_field, "description"):
        description = field.native_field.description  # type: ignore
        field_info["description"] = description

    # Get renderer and render the field
    renderer = get_field_renderer(field_info)
    return renderer(
        key=field_name,
        value=value,
        label=label,
        **field_info,
    )


TForm = TypeVar("TForm", bound="BaseModel")


@overload
def render_model_form(
    model_or_instance: type[TForm], *, readonly: bool = False
) -> TForm: ...


@overload
def render_model_form(model_or_instance: TForm, *, readonly: bool = False) -> TForm: ...


def render_model_form(model_or_instance, *, readonly: bool = False) -> Any:
    """Render a complete form for a model class or instance.

    Args:
        model_or_instance: Either a model class or an instance of it
        readonly: Whether to render in read-only mode

    Returns:
        An instance of the model with updated values
    """
    # Determine if we have a class or an instance
    if isinstance(model_or_instance, type):
        # We received a class
        model_class = model_or_instance
        instance = model_class()  # Create a default instance
    else:
        # We received an instance
        instance = model_or_instance
        model_class = instance.__class__
    if readonly:
        render_model_readonly(model_class, instance)
        return instance  # No changes in read-only mode

    # Interactive form rendering
    result = {}

    for field in fieldz.fields(model_class):
        field_name = field.name
        # Use _get_with_default to handle 'MISSING' values
        current_value = _get_with_default(instance, field_name, field)

        st.subheader(field_name.replace("_", " ").title())

        # Display field description if available
        description = None
        if hasattr(field, "metadata") and "description" in field.metadata:
            description = field.metadata["description"]
        elif hasattr(field, "native_field") and hasattr(
            field.native_field, "description"
        ):
            description = field.native_field.description  # type: ignore

        if description:
            st.caption(description)

        # Render the field and store the result
        result[field_name] = render_model_field(model_class, field_name, current_value)

    # Create a new instance with updated values
    return fieldz.replace(instance, **result)


if __name__ == "__main__":
    from typing import Literal

    from pydantic import BaseModel, Field

    from streambricks.helpers import run

    class SubModel(BaseModel):
        """Test submodel."""

        name: str
        value: int | float
        active: bool = True

    class TestModel(BaseModel):
        """Test model."""

        status: int | str | bool = Field(
            2, description="A field that can be either int, str, or bool"
        )
        optional_text: str | None = Field(None, description="Optional text field")

        # Lists with various types
        tags: list[str] = Field(default_factory=list, description="A list of string tags")
        numbers: list[int | float] = Field(
            default_factory=list, description="A list of numbers (int or float)"
        )

        # Nested structures
        settings: list[SubModel] = Field(
            default_factory=list, description="A list of nested models"
        )

        # Combined with literals
        priorities: list[Literal["Low", "Medium", "High"]] = Field(
            default_factory=list, description="A list of priority levels"
        )

    def demo():
        st.title("Pydantic Form Demo")

        # Initialize or get model from session state
        if "model" not in st.session_state:
            st.session_state.model = TestModel(status=2, optional_text=None)

        # Render the complete form and update the model
        st.session_state.model = render_model_form(TestModel)

        # Display current model state
        with st.expander("Current Model State", expanded=True):
            st.json(st.session_state.model.model_dump_json(indent=2))

    run(demo)
