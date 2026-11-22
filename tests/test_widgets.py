"""Tests."""

from __future__ import annotations

from streamlit.testing.v1 import AppTest


def test_nothing():
    pass


def _model_form_app():
    from enum import Enum

    from pydantic import BaseModel
    import streamlit as st

    import streambricks as sb

    class Color(Enum):
        RED = "red"
        BLUE = "blue"

    class Settings(BaseModel):
        name: str = "foo"
        count: int = 3
        enabled: bool = True
        color: Color = Color.RED

    result = sb.model_edit(Settings)
    st.session_state["result"] = result


def test_model_edit_renders_fields():
    at = AppTest.from_function(_model_form_app).run()
    assert not at.exception
    assert at.text_input[0].value == "foo"
    assert at.number_input[0].value == 3  # noqa: PLR2004
    assert at.checkbox[0].value is True
    at.text_input[0].input("bar").run()
    at.number_input[0].set_value(5).run()
    result = at.session_state["result"]
    assert result.name == "bar"
    assert result.count == 5  # noqa: PLR2004


def _dataclass_form_app():
    from dataclasses import dataclass

    import streamlit as st

    import streambricks as sb

    @dataclass
    class Point:
        x: int = 1
        label: str = "origin"

    st.session_state["result"] = sb.model_edit(Point(x=2))
    sb.model_display(Point, Point(x=7, label="shown"))


def test_model_edit_supports_dataclasses():
    at = AppTest.from_function(_dataclass_form_app).run()
    assert not at.exception
    assert at.session_state["result"].x == 2  # noqa: PLR2004
    assert "shown" in [t.value for t in at.text]


def _multiselect_app():
    import streamlit as st

    import streambricks as sb

    items = [sb.MultiSelectItem("Apple", 1), sb.MultiSelectItem("Banana", 2)]
    selected = sb.multiselect("Fruits", items, state_key="fruits", default_all=True)
    st.session_state["selected"] = [item.value for item in selected]


def test_multiselect_default_all():
    at = AppTest.from_function(_multiselect_app).run()
    assert not at.exception
    assert at.session_state["selected"] == [1, 2]


def _state_app():
    import streamlit as st

    from tests.state_models import Counter

    state = Counter.get()
    state.value += 1
    st.session_state["counter_value"] = Counter.get().value


def test_state_persists_across_reruns():
    at = AppTest.from_function(_state_app).run()
    assert at.session_state["counter_value"] == 1
    at.run()
    assert at.session_state["counter_value"] == 2  # noqa: PLR2004


def _bind_kwargs_app():
    import streamlit as st

    import streambricks as sb

    def greet(name: str, greeting: str = "Hello") -> str:
        return f"{greeting}, {name}!"

    bound = sb.bind_kwargs_as_widget(greet, kwargs_to_bind=["greeting"])
    st.session_state["out"] = bound("World")


def test_bind_kwargs_as_widget():
    at = AppTest.from_function(_bind_kwargs_app).run()
    assert not at.exception
    assert at.session_state["out"] == "Hello, World!"
