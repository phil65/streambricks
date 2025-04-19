import streamlit as st


HIDE_SIDEBAR = """\
<style>
[data-testid="stSidebar"][aria-expanded="true"] {display: none;}
[data-testid="stSidebar"][aria-expanded="false"] {display: none;}
</style>
"""


def set_sidebar_width(width: int):
    st.markdown(
        f"""\
<style>
[data-testid="stSidebar"][aria-expanded="true"] > div:first-child {{
    width: {width}px;
}}
[data-testid="stSidebar"][aria-expanded="false"] > div:first-child {{
    width: {width}px;
    margin-left: -{width}px;
}}
</style>
        """,
        unsafe_allow_html=True,
    )


def hide_sidebar():
    st.markdown(HIDE_SIDEBAR, unsafe_allow_html=True)
