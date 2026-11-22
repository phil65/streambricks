# StreamBricks

[![PyPI License](https://img.shields.io/pypi/l/streambricks.svg)](https://pypi.org/project/streambricks/)
[![Package status](https://img.shields.io/pypi/status/streambricks.svg)](https://pypi.org/project/streambricks/)
[![Monthly downloads](https://img.shields.io/pypi/dm/streambricks.svg)](https://pypi.org/project/streambricks/)
[![Distribution format](https://img.shields.io/pypi/format/streambricks.svg)](https://pypi.org/project/streambricks/)
[![Wheel availability](https://img.shields.io/pypi/wheel/streambricks.svg)](https://pypi.org/project/streambricks/)
[![Python version](https://img.shields.io/pypi/pyversions/streambricks.svg)](https://pypi.org/project/streambricks/)
[![Implementation](https://img.shields.io/pypi/implementation/streambricks.svg)](https://pypi.org/project/streambricks/)
[![Releases](https://img.shields.io/github/downloads/phil65/streambricks/total.svg)](https://github.com/phil65/streambricks/releases)
[![Github Contributors](https://img.shields.io/github/contributors/phil65/streambricks)](https://github.com/phil65/streambricks/graphs/contributors)
[![Github Forks](https://img.shields.io/github/forks/phil65/streambricks)](https://github.com/phil65/streambricks/forks)
[![Github Issues](https://img.shields.io/github/issues/phil65/streambricks)](https://github.com/phil65/streambricks/issues)
[![Github Issues](https://img.shields.io/github/issues-pr/phil65/streambricks)](https://github.com/phil65/streambricks/pulls)
[![Github Watchers](https://img.shields.io/github/watchers/phil65/streambricks)](https://github.com/phil65/streambricks/watchers)
[![Github Stars](https://img.shields.io/github/stars/phil65/streambricks)](https://github.com/phil65/streambricks/stars)
[![Github Repository size](https://img.shields.io/github/repo-size/phil65/streambricks)](https://github.com/phil65/streambricks)
[![Github last commit](https://img.shields.io/github/last-commit/phil65/streambricks)](https://github.com/phil65/streambricks/commits)
[![Github release date](https://img.shields.io/github/release-date/phil65/streambricks)](https://github.com/phil65/streambricks/releases)
[![Github language count](https://img.shields.io/github/languages/count/phil65/streambricks)](https://github.com/phil65/streambricks)
[![Github commits this month](https://img.shields.io/github/commit-activity/m/phil65/streambricks)](https://github.com/phil65/streambricks)
[![Package status](https://codecov.io/gh/phil65/streambricks/branch/main/graph/badge.svg)](https://codecov.io/gh/phil65/streambricks/)
[![PyUp](https://pyup.io/repos/github/phil65/streambricks/shield.svg)](https://pyup.io/repos/github/phil65/streambricks/)

[Read the documentation!](https://phil65.github.io/streambricks/)

Reusable widgets and helpers for [Streamlit](https://streamlit.io/) apps. The core
feature is automatic form generation: pass a Pydantic model (or a dataclass or another
[fieldz](https://github.com/pyapp-kit/fieldz)-supported class) and get an editable or
read-only form back, including nested models, unions, enums, literals, lists and sets.

## Installation

```bash
pip install streambricks
# optional extras
pip install "streambricks[auth]"  # Google / Microsoft login via st.login
pip install "streambricks[llm]"   # LLM model selector (tokonomics)
```

## Quickstart

```python
from typing import Literal

from pydantic import BaseModel, Field
import streamlit as st

import streambricks as sb


class Settings(BaseModel):
    name: str = Field(default="World", description="Who to greet")
    retries: int = Field(default=3, ge=0, le=10)
    mode: Literal["fast", "safe"] = "fast"
    tags: list[str] = Field(default_factory=list)


def main():
    settings = sb.model_edit(Settings)  # returns an updated Settings instance
    st.write(f"Hello, {settings.name}!")
    sb.model_display(Settings, settings)  # read-only view


sb.run(main)
```

Run it with `streamlit run app.py`, or with `python app.py`: `sb.run` starts
Streamlit for you when called outside of it.

## Features

### Model forms

- `model_edit(model_or_instance, *, readonly=False, exclude=None)`: render a form for a
  class (defaults are used) or an instance, return the edited instance.
- `model_display(model_class, instance)`: read-only rendering.
- Field descriptions (`Field(description=...)`, or attribute docstrings with
  `ConfigDict(use_attribute_docstrings=True)`) become help texts;
  fields with `json_schema_extra={"category": ...}` are grouped into tabs.

### Typed session state

```python
# app_state.py
import streambricks as sb


class AppState(sb.State):
    counter: int = 0
```

```python
# app.py
import streamlit as st

from app_state import AppState

state = AppState.get()  # stored in st.session_state, survives reruns
if st.button("Increment"):
    state.counter += 1
st.write(state.counter)
state.form()  # edit the state with a generated form
```

`State` subclasses also provide `set_state(value=...)` and `reset()`. Define them in a
separate module: classes defined in the main script are recreated on every rerun, which
resets the stored state.

### Function kwargs as widgets

```python
import streamlit as st
import streambricks as sb


def plot(title: str, points: int = 10, smooth: bool = False) -> str:
    return f"{title}: {points} points, smooth={smooth}"


configured = sb.bind_kwargs_as_widget(
    plot, kwargs_to_bind=["points", "smooth"], title="Plot options"
)
st.write(configured("My plot"))
```

### Other widgets

```python
import streambricks as sb

items = [
    sb.MultiSelectItem("Apple", "apple", description="Red fruit"),
    sb.MultiSelectItem("Banana", "banana"),
]
selected = sb.multiselect("Fruits", items, state_key="fruits")  # list[MultiSelectItem]

image = sb.image_capture()  # file upload or camera, returns UploadedFile | None

model = sb.model_selector(providers=["openai"])  # needs the "llm" extra

sb.set_sidebar_width(400)
sb.hide_sidebar()
```

### Authentication

Thin, typed wrappers around Streamlit's built-in authentication (`st.login`, configured
in `.streamlit/secrets.toml`; requires the `auth` extra):

```python
import streamlit as st
import streambricks as sb

user = sb.google_login("Login with Google")  # GoogleUser | None
# user = sb.microsoft_login()                # MicrosoftUser | None
if user:
    sb.profile_widget(user, size="medium")


@sb.requires_login(unauthorized_handler="Please log in first")
def dashboard():
    st.write("Protected content")


dashboard()
```

`get_current_user()` returns the logged-in user (or `None`) without rendering anything.
