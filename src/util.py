from PIL import Image
import streamlit as st


@st.cache_data(show_spinner=False, persist=True)
def add_logo():
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                background-image: url(https://upload.wikimedia.org/wikipedia/commons/a/a4/Toronto-Dominion_Bank_logo.svg);
                background-repeat: no-repeat;
                background-size: 15%;
                padding-top: 0px;
                background-position: 20px 20px;
            }
            [data-testid="stSidebarNav"]::before {
                content: "ADRES";
                margin-left: 70px;
                margin-top: 0px;
                font-size: 35px;
                position: relative;
                top: 11px;
                color: #54B948;
                font-weight: bold;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False, persist=True)
def get_favicon():
    image = Image.open('./static/favicon.png')
    return image


def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])
