"""Primitive type handlers for Pydantic form fields."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal, get_args, get_origin

import fieldz


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


def is_set_type(annotation: Any) -> bool:
    """Check if the annotation represents a set type."""
    if annotation is set:
        return True
    origin = get_origin(annotation)
    return origin is set


def is_sequence_type(annotation: Any) -> bool:
    """Check if an annotation represents a sequence type (except sets)."""
    origin = get_origin(annotation)
    if origin in (list, tuple, Sequence):
        return True

    return annotation in (list, tuple, Sequence)


def get_with_default(obj: Any, field_name: str, field_info: Any = None) -> Any:  # noqa: PLR0911
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


def is_dataclass_like(annotation: Any) -> bool:
    """Check if a type is a dataclass-like object (Pydantic model, attrs, etc.)."""
    if not isinstance(annotation, type):
        return False
    try:
        fields = fieldz.fields(annotation)
        # If we get fields, it's a dataclass-like object
        return len(fields) > 0
    except Exception:  # noqa: BLE001
        # If fieldz can't handle it, it's not a dataclass-like object
        return False


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

    return model_class(**default_values)


def get_description(field: fieldz.Field) -> str | None:
    if "description" in field.metadata:
        return field.metadata["description"]
    if hasattr(field.native_field, "description"):
        return field.native_field.description  # type: ignore
    return None


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
