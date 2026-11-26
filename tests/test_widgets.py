"""Tests."""

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


def _requires_login_app():
    import streamlit as st

    import streambricks as sb

    @sb.requires_login(unauthorized_handler="Please log in first")
    def page():
        st.write("secret")

    page()


def test_requires_login_without_auth_configured():
    at = AppTest.from_function(_requires_login_app).run()
    assert not at.exception
    assert [e.value for e in at.error] == ["Please log in first"]


def _readonly_collections_app():
    from enum import Enum

    from pydantic import BaseModel

    import streambricks as sb

    class Color(Enum):
        RED = "red"
        BLUE = "blue"

    class Collections(BaseModel):
        tags: list[str] = ["alpha", "beta"]
        items: set[str] = {"one", "two"}
        colors: set[Color] = {Color.RED}

    sb.model_display(Collections, Collections())


def test_model_display_renders_nonempty_sequence_and_set():
    at = AppTest.from_function(_readonly_collections_app).run()
    assert not at.exception
    texts = {t.value for t in at.text}
    assert {"alpha", "beta", "one", "two", "RED"}.issubset(texts)


def _datetime_form_app():
    from datetime import datetime

    from pydantic import BaseModel
    import streamlit as st

    import streambricks as sb

    class Event(BaseModel):
        starts_at: datetime = datetime(2025, 1, 2, 14, 30, 0)

    st.session_state["result"] = sb.model_edit(Event)


def test_model_edit_datetime_field_renders_datetime():
    from datetime import datetime

    at = AppTest.from_function(_datetime_form_app).run()
    assert not at.exception
    assert len(at.date_input) == 1
    assert len(at.time_input) == 1
    starts_at = at.session_state["result"].starts_at
    assert type(starts_at) is datetime
    assert starts_at == datetime(2025, 1, 2, 14, 30, 0)


def _union_form_app():
    from typing import Literal

    from pydantic import BaseModel
    import streamlit as st

    import streambricks as sb

    class UnionModel(BaseModel):
        mode_or_id: Literal["fast", "safe"] | int = 5
        tags_or_label: list[str] | str = "hello"
        opt_tags: list[str] | None = ["a", "b"]
        flag_or_count: int | bool = True

    st.session_state["result"] = sb.model_edit(UnionModel)


def test_model_edit_union_with_literal_and_generics():
    at = AppTest.from_function(_union_form_app).run()
    assert not at.exception
    res = at.session_state["result"]
    assert res.mode_or_id == 5  # noqa: PLR2004
    assert res.tags_or_label == "hello"
    assert res.opt_tags == ["a", "b"]
    assert res.flag_or_count is True


def _sequence_delete_app():
    import streamlit as st

    from streambricks.widgets.sequence import sequence_widget

    res = sequence_widget("Tags", str, value=["apple", "banana", "cherry"], key="tags")
    st.session_state["res"] = list(res)


def test_sequence_widget_delete_removes_selected_item():
    at = AppTest.from_function(_sequence_delete_app).run()
    assert not at.exception
    assert at.session_state["res"] == ["apple", "banana", "cherry"]
    # Button 0 is "Add Item"; button 1 is the delete button for item 0 ("apple")
    at.button[1].click().run()
    assert not at.exception
    assert at.session_state["res"] == ["banana", "cherry"]


def _open_set_delete_app():
    import streamlit as st

    from streambricks.widgets.model_widget.main import render_set_field

    res = render_set_field(key="tags", value={"apple", "banana", "cherry"}, type=set[str])
    st.session_state["res"] = set(res)


def test_open_set_delete_removes_selected_item():
    at = AppTest.from_function(_open_set_delete_app).run()
    assert not at.exception
    initial_order = list(at.session_state["tags_items"])
    # Button 0 is "Add Item"; button 1 is the delete button for item 0
    at.button[1].click().run()
    assert not at.exception
    assert at.session_state["tags_items"] == initial_order[1:]
    assert at.session_state["res"] == set(initial_order[1:])
