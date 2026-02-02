import streamlit as st


def page_header(title: str, subtitle: str | None = None):
    st.header(title)
    if subtitle:
        st.caption(subtitle)


def section(title: str, icon: str = "", divider: bool = True):
    if divider:
        st.write("---")
    st.subheader(f"{icon} {title}" if icon else title)


def card_container(border: bool = True):
    return st.container(border=border)


def responsive_columns(ratios):
    """
    Use poucos elementos (máx 3) para não quebrar no mobile
    """
    return st.columns(ratios)


def empty_state(message: str):
    st.info(message)
