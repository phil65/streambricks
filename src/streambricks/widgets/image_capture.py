"""Model selector component for streamlit applications."""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st


if TYPE_CHECKING:
    from streamlit.runtime.uploaded_file_manager import UploadedFile


def image_capture(
    *,
    image_label: str | None = None,
    camera_label: str | None = None,
    supported_types: list[str] | None = None,
) -> UploadedFile | None:
    """Capture an image from a file upload or camera.

    Args:
        image_label: Label for the file upload widget.
        camera_label: Label for the camera input widget.
        supported_types: List of supported file types for image upload.

    Returns:
        Uploaded file or None if not selected.
    """
    tab1, tab2 = st.tabs(["Upload file", "Use camera"])
    with tab1:
        types_ = supported_types or ["pdf", "png", "jpg", "jpeg"]
        supported_str = f"Supported file types: {', '.join(types_)}"
        uploaded_file = st.file_uploader(
            image_label or "Upload picture", type=types_, help=supported_str
        )
    with tab2:
        camera_file = st.camera_input(
            camera_label or "Use camera to capture image",
        )
    if uploaded_file is not None:
        return uploaded_file
    if camera_file is not None:
        return camera_file
    return None
