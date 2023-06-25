import streamlit as st
import pandas as pd

import util


@st.cache_data(show_spinner=False, persist=True)
def load_data(path):
    df = pd.read_csv(path, dtype={'acct_no': 'str'})
    return df


if __name__ == '__main__':
    st.set_page_config(
        layout='wide',
        initial_sidebar_state='expanded',
        page_title='ADRES | Upload Data',
        page_icon=util.get_favicon(),
    )

    # Sidebar
    st.session_state['logo'] = False
    util.add_logo()

    st.markdown('# Upload Data')
    st.write(
        '''
        ##### Upload your file and then go to the next tabs for visualizations
        '''
    )

    uploaded_data = st.file_uploader(
        label='',
        type='.csv',
        accept_multiple_files=False,
    )

    if uploaded_data is not None:
        st.session_state['uploaded'] = True
        st.session_state['file_name'] = uploaded_data.name
        st.session_state['df'] = load_data(uploaded_data)
        # Inputs
        st.session_state['view_type'] = '$ Amount'
        st.session_state['cumulative'] = True
        st.session_state['product_type'] = False
        st.session_state['forecast_windows'] = [0.5, 1, 2, 3, 4, 5, 6, 7, 8]
        st.session_state['forecast_window'] = st.session_state['forecast_windows'][5] * 12
        st.session_state['discount_rate'] = 3.6
        st.session_state['wrtoff_dates'] = sorted(st.session_state['df']['wrtoff_dt'].unique().tolist())
        st.session_state['wrtoff_date'] = st.session_state['wrtoff_dates'][-2:]
        
    if 'df' in st.session_state:
        if not st.session_state['uploaded']:
            st.success('An example file is already uploaded!')
        else:
            st.success('Your file was uploaded!')
    # If an example is required
    else:
        st.session_state['uploaded'] = False
        st.session_state['file_name'] = 'example.csv'
        st.session_state['df'] = load_data('./streamlit/example.csv')
        # Inputs
        st.session_state['view_type'] = '$ Amount'
        st.session_state['cumulative'] = True
        st.session_state['product_type'] = False
        st.session_state['forecast_windows'] = [0.5, 1, 2, 3, 4, 5, 6, 7, 8]#[6, 12, 24, 36, 48, 60, 72, 84, 96]
        st.session_state['forecast_window'] = st.session_state['forecast_windows'][5] * 12
        st.session_state['discount_rate'] = 3.6
        st.session_state['wrtoff_dates'] = sorted(st.session_state['df']['wrtoff_dt'].unique().tolist())
        st.session_state['wrtoff_date'] = st.session_state['wrtoff_dates'][-2:]
        st.success('An example file is already uploaded!')

    with st.expander("Click for '{}' file preview".format(st.session_state['file_name']), False):
        st.dataframe(st.session_state['df'])
        # st.session_state['df'] = st.experimental_data_editor(st.session_state['df'])
