# Profile Widget

The profile widget provides a simple way to display user profile information in Streamlit apps. It shows a profile picture (if available) or generates an avatar with user initials and displays the user's name.

## Features

- Uses Google profile picture if available
- Generates a colorful avatar with user initials if no picture is available
- Supports different sizes: small, medium, large
- Optional name display
- Custom name override option

## Usage

```python
import streamlit as st
from streambricks import profile_widget, google_login, microsoft_login

# Login with your preferred method
user = google_login("Login to see profile")
# OR
# user = microsoft_login("Login with Microsoft")

if user:
    # Basic usage
    profile_widget(user)
    
    # Customize size
    profile_widget(user, size="medium")  # Options: "small", "medium", "large"
    
    # Without name
    profile_widget(user, show_name=False)
    
    # Custom display name
    profile_widget(user, display_name="Custom Name")
```

## API Reference

```python
def profile_widget(
    user: GoogleUser | MicrosoftUser | None = None, 
    display_name: str | None = None,
    size: Literal["small", "medium", "large"] = "small",
    show_name: bool = True,
    key: str | None = None,
) -> None:
```

### Parameters

- **user**: A `GoogleUser` or `MicrosoftUser` object obtained from login methods
- **display_name**: Optional custom name to display instead of the user's name
- **size**: Size of the avatar ("small", "medium", or "large")
- **show_name**: Whether to show the name beside the avatar
- **key**: Optional unique key for the Streamlit widget

## Examples

### Different Sizes

```python
st.write("Available sizes:")
col1, col2, col3 = st.columns(3)

with col1:
    st.caption("Small (default)")
    profile_widget(user, size="small")

with col2:
    st.caption("Medium")
    profile_widget(user, size="medium")

with col3:
    st.caption("Large")
    profile_widget(user, size="large")
```

### Usage in Header

```python
col1, col2 = st.columns([1, 5])

with col1:
    profile_widget(user, show_name=False, size="medium")
    
with col2:
    st.title("Dashboard")
```