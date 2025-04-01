"""Primitive type handlers for Pydantic form fields."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Any, Literal, get_args, get_origin

import fieldz


# For reference, these are the fieldz classes:
#
# @dataclasses.dataclass(**DC_KWARGS)
# class Constraints:
#     gt: int | float | None = None
#     ge: int | float | None = None
#     lt: int | float | None = None
#     le: int | float | None = None
#     multiple_of: int | float | None = None
#     min_length: int | None = None  # for str
#     max_length: int | None = None  # for str
#     max_digits: int | None = None  # for decimal
#     decimal_places: int | None = None  # for decimal
#     pattern: str | None = None
#     deprecated: bool | None = None
#     tz: bool | None = None
#     predicate: Callable[[Any], bool] | None = None
#     # enum: list[Any] | None = None
#     # const: Any | None = None
#
#     def __rich_repr__(self) -> Iterable[tuple[str, Any]]:
#         for name, val in dataclasses.asdict(self).items():
#             if val is not None:
#                 yield name, val
#
#
# @dataclasses.dataclass(**DC_KWARGS)
# class Field(Generic[_T]):
#     MISSING: ClassVar[Literal[_MISSING_TYPE.MISSING]] = _MISSING_TYPE.MISSING
#
#     name: str,
#     type
#     description: str | None = None
#     title: str | None = None
#     default: _T | Literal[_MISSING_TYPE.MISSING] = MISSING
#     default_factory: Callable[[], _T] | Literal[_MISSING_TYPE.MISSING] = MISSING
#     repr: bool = True
#     hash: bool | None = None
#     init: bool = True
#     compare: bool = True
#     metadata: Mapping[Any, Any] = dataclasses.field(default_factory=dict)
#     kw_only: bool = False
#     # extra
#     frozen: bool = False
#     native_field: Any | None = dataclasses.field(
#         default=None, compare=False, repr=False
#     )
#     constraints: Constraints | None = None

#     # populated during parse_annotated
#     annotated_type: builtins.type[_T] | None = dataclasses.field(
#         default=None, repr=False, compare=False
#     )


def unpack_annotated(annotation: Any) -> Any:
    """Unpack an Annotated type annotation to its base type."""
    if get_origin(annotation) is Annotated and (args := get_args(annotation)):
        return args[0]
    return annotation


def is_literal_type(annotation: Any) -> bool:
    """Check if a type annotation is a Literal type."""
    # Check directly against the origin or special attribute
    return (
        get_origin(annotation) is Literal
        or getattr(annotation, "__origin__", None) is Literal
    )


def is_union_type(annotation: Any) -> bool:
    import typing

    origin = get_origin(annotation)
    # Direct identity check for typing.Union
    if origin is typing.Union:
        return True

    # Check for Python 3.10+ pipe syntax union
    if hasattr(annotation, "__class__") and annotation.__class__.__name__ == "UnionType":
        return True

    # For Python 3.10+ unions detected via get_origin
    return bool(
        origin is not None
        and hasattr(origin, "__class__")
        and origin.__class__.__name__ == "UnionType"
    )


def is_optional_type(annotation: Any) -> bool:
    """Check if a type annotation is an Optional type (T | None)."""
    if not is_union_type(annotation):
        return False

    args = get_args(annotation)
    return type(None) in args


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


def get_with_default(obj: Any, field_name: str, field_info: fieldz.Field) -> Any:  # noqa: PLR0911
    """Get field value with appropriate default if it's missing."""
    # Get the raw value
    value = getattr(obj, field_name, None)

    # If value isn't MISSING, return it as is
    if value != fieldz.Field.MISSING:
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
        if field.default != fieldz.Field.MISSING:
            default_values[field_name] = field.default
            has_default = True
        elif field.default_factory != fieldz.Field.MISSING:
            try:
                default_values[field_name] = field.default_factory()  # pyright: ignore
                has_default = True
            except Exception:  # noqa: BLE001
                # If default_factory fails, fall back to type-based defaults
                pass

        if not has_default:
            default_values[field_name] = get_default_value(field.type)

    return model_class(**default_values)


def get_default_value(field_type: Any):  # noqa: PLR0911
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
    if isinstance(field_type, type):
        if issubclass(field_type, str):
            return ""
        if issubclass(field_type, int):
            return 0
        if issubclass(field_type, float):
            return 0.0
        if issubclass(field_type, bool):
            return False
        if is_dataclass_like(field_type):
            return create_default_instance(field_type)
    return None  #  or field_type()?


def get_description(field: fieldz.Field) -> str | None:
    if "description" in field.metadata:
        return field.metadata["description"]
    if hasattr(field.native_field, "description"):
        return field.native_field.description  # type: ignore
    return None


def add_new_item(items_list: list, item_type: Any) -> None:
    """Add a new item to a list based on its type."""
    if is_dataclass_like(item_type):
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


def get_inner_type(field_info: Any) -> Any:
    annotation = field_info.get("type") or field_info.get("annotation")
    try:
        return get_args(annotation)[0]  # Get type of set items
    except (IndexError, TypeError):
        return Any


def get_field(model_class, field_name: str) -> fieldz.Field:
    field = next(
        (f for f in fieldz.fields(model_class) if f.name == field_name),
        None,
    )
    if field is None:
        error_msg = f"Field {field_name} not found in {model_class.__name__}"
        raise ValueError(error_msg)
    return field


def get_union_type_options(annotation: Any) -> list[tuple[Any, str]]:
    """Analyze a union type and extract individual types with their descriptions.

    Args:
        annotation: Type annotation to analyze

    Returns:
        List of tuples containing (resolved_type, type_description)
    """
    type_options = []

    # Process each union member
    for arg in get_args(annotation):
        # Handle Annotated type that contains a union
        if get_origin(arg) is Annotated:
            annotated_args = get_args(arg)
            if not annotated_args:
                continue

            # Get the inner type (first arg of Annotated)
            inner = annotated_args[0]

            # Handle pipe-syntax union (Python 3.10+)
            if inner.__class__.__name__ == "UnionType":
                # Extract each union member - use __args__ attribute for pipe unions
                for union_member in inner.__args__:
                    description = (
                        union_member.__name__
                        if hasattr(union_member, "__name__")
                        else str(union_member)
                    )
                    type_options.append((union_member, description))
            elif is_union_type(inner):
                # Handle traditional Union types
                for union_member in get_args(inner):
                    description = (
                        union_member.__name__
                        if hasattr(union_member, "__name__")
                        else str(union_member)
                    )
                    type_options.append((union_member, description))
            else:
                # Single type in Annotated
                description = inner.__name__ if hasattr(inner, "__name__") else str(inner)
                type_options.append((inner, description))

        # Handle Literal types
        elif is_literal_type(arg):
            values = ", ".join(
                f'"{v}"' if isinstance(v, str) else str(v) for v in get_args(arg)
            )
            description = f"Literal[{values}]"
            type_options.append((arg, description))

        # Handle None type
        elif arg is type(None):
            type_options.append((arg, "None"))

        # Handle regular types
        else:
            description = arg.__name__ if hasattr(arg, "__name__") else str(arg)
            type_options.append((arg, description))

    return type_options


if __name__ == "__main__":
    from pydantic import BaseModel

    class SubModel(BaseModel):
        """Test submodel."""

        name: str
        value: int | float
        active: bool = True

    print(create_default_instance(SubModel))
