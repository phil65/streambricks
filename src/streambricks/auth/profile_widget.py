from __future__ import annotations

import base64
import functools
import hashlib
from io import BytesIO
from typing import Literal

from PIL import Image, ImageDraw, ImageFont
import streamlit as st

from streambricks.auth.models import GoogleUser, MicrosoftUser


@st.cache_data(ttl=3600, show_spinner=False)
def _generate_avatar_image(
    initials: str,
    bg_color: str | tuple[int, int, int] = "#1f77b4",
    text_color: str | tuple[int, int, int] = "white",
    size: int = 100,
) -> Image.Image:
    """Generate an avatar image with user initials.

    Args:
        initials: The text to display on the avatar (usually initials)
        bg_color: Background color as hex string or RGB tuple
        text_color: Text color as hex string or RGB tuple
        size: Size of the image in pixels

    Returns:
        PIL Image with generated avatar
    """
    # Create a square image with the specified background color
    img = Image.new("RGB", (size, size), bg_color)
    draw = ImageDraw.Draw(img)

    # Try to load a font, fall back to default if not available
    font_size = int(size * 0.4)  # 40% of image size
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    text_width, text_height = draw.textbbox((0, 0), initials, font=font)[2:]
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    draw.text((x, y), initials, fill=text_color, font=font)
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size, size), fill=255)
    img.putalpha(mask)

    return img


def _get_initials(name: str) -> str:
    """Extract initials from a name.

    Args:
        name: Full name of the user

    Returns:
        Initials (up to 2 characters)
    """
    parts = name.strip().split()
    if not parts:
        return "?"

    if len(parts) == 1:
        return parts[0][0].upper()

    return (parts[0][0] + parts[-1][0]).upper()


@functools.lru_cache(maxsize=128)
def _get_color_from_string(s: str) -> str:
    """Generate a consistent color from a string.

    Args:
        s: Input string (like user ID)

    Returns:
        Hex color code
    """
    # Use a hash function to get a reproducible integer from the string
    hash_obj = hashlib.md5(s.encode())
    hash_int = int.from_bytes(hash_obj.digest()[:4], "little")

    # Select from a set of good UI colors (excluding very light ones)
    colors = [
        "#1f77b4",  # blue
        "#ff7f0e",  # orange
        "#2ca02c",  # green
        "#d62728",  # red
        "#9467bd",  # purple
        "#8c564b",  # brown
        "#e377c2",  # pink
        "#7f7f7f",  # gray
        "#bcbd22",  # olive
        "#17becf",  # teal
    ]

    return colors[hash_int % len(colors)]


@st.cache_data(ttl=3600, show_spinner=False)
def _image_to_base64(img_hash: int, img: Image.Image) -> str:
    """Convert a PIL Image to a base64 string.

    Args:
        img_hash: Hash of the image parameters for caching
        img: PIL Image object

    Returns:
        Base64 encoded string of the image
    """
    # The img_hash parameter is only used for caching and isn't used in the function
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def profile_widget(
    user: GoogleUser | MicrosoftUser | None = None,
    display_name: str | None = None,
    size: Literal["small", "medium", "large"] = "small",
    show_name: bool = True,
    key: str | None = None,
) -> None:
    """Display a profile widget with user avatar and name.

    Args:
        user: GoogleUser or MicrosoftUser object
        display_name: Optional name override to display instead of user's name
        size: Size of the avatar image ("small", "medium", or "large")
        show_name: Whether to show the name next to the avatar
        key: Optional key for the Streamlit widget

    Returns:
        None
    """
    if user is None:
        return

    size_map = {"small": 32, "medium": 48, "large": 64}
    img_size = size_map[size]
    name = display_name or user.name
    css = f"""
    <style>
    .profile-widget-{key if key else "default"} {{
        display: flex;
        align-items: center;
        margin: 5px 0;
    }}
    .avatar-{key if key else "default"} {{
        border-radius: 50%;
        width: {img_size}px;
        height: {img_size}px;
        object-fit: cover;
    }}
    .profile-name-{key if key else "default"} {{
        margin-left: 10px;
        font-size: {int(img_size * 0.4)}px;
    }}
    </style>
    """

    img_src = ""
    if isinstance(user, GoogleUser) and user.picture:
        img_src = user.picture
    else:
        # Generate avatar with initials
        initials = _get_initials(name)
        color = _get_color_from_string(user.user_id)
        # Double size for better quality
        avatar_img = _generate_avatar_image(initials, color, size=img_size * 2)
        # Create a hash of the parameters for caching the base64 conversion
        img_hash = hash((initials, color, img_size))
        img_src = f"data:image/png;base64,{_image_to_base64(img_hash, avatar_img)}"

    # HTML for the widget
    html = f"""
    {css}
    <div class="profile-widget-{key if key else "default"}">
        <img src="{img_src}" class="avatar-{key if key else "default"}" alt="User Avatar">
        {
        f'<span class="profile-name-{key if key else "default"}">{name}</span>'
        if show_name
        else ""
    }
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)
