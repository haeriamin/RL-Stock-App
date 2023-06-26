import os
import warnings
import pandas as pd
import streamlit as st
import pandas_market_calendars as mcal

from src import params, data, model, agent, util


warnings.filterwarnings("ignore")


def run(data_params, env_kwargs, model_name, date):
    # Get data
    test = data.main(
        stocks = data_params['stocks'],
        date = date,
    )

    # Create environment
    test_env = model.StockPortfolioEnv(
        df = test,
        **env_kwargs
    )

    # Predict
    df_daily_return_ppo, df_actions_ppo = agent.Agent.predict(
        model_name = model_name,
        environment = test_env,
        cwd = os.path.join('src', model_name),
        deterministic = True,
    )
    st.write('Actions')
    st.dataframe(df_actions_ppo)

    # Account value calculation
    ppo_cumprod = (df_daily_return_ppo.daily_return + 1).cumprod() - 1
    account_value = env_kwargs['initial_amount'] + (env_kwargs['initial_amount'] * ppo_cumprod)

    st.write('Account value')
    st.dataframe(account_value)

    # return account_value.iat[-1], df_actions_ppo.iloc[-1, :].values.flatten().tolist()


def main():
    st.set_page_config(
        layout='wide',
        initial_sidebar_state='expanded',
        page_title='Home',
        # page_icon=':bank:',
        page_icon=util.get_favicon(),
    )
    st.markdown('# RL Stock App')

    amount_AAPL = st.sidebar.number_input(
        'AAPL share [$]',
        value = 5.,
        step = 0.01
    )
    amount_TSLA = st.sidebar.number_input(
        'TSLA share [$]',
        value = 5.,
        step = 0.01
    )
    commission_perc = st.sidebar.number_input(
        'Commission percentage [%]',
        value = 2.,
        step = 0.01
    )
    initial_amount = amount_AAPL + amount_TSLA
    initial_allocation_1 = amount_AAPL / initial_amount
    initial_allocation_2 = amount_TSLA / initial_amount

    st.divider()
    st.write(pd.to_datetime('today').tz_localize('EST'))

    if st.button('Train'):
        st.write('Model was trained!')

    if st.button('Predict'):
        # Get params
        data_params, env_params, model_params, _ = params.main()

        # Last business dates
        nyse = mcal.get_calendar('NYSE')

        end_date = pd.to_datetime('today').tz_localize('EST')
        start_date = end_date - pd.to_timedelta(30, unit='d')
        days = nyse.schedule(start_date=start_date, end_date=end_date)

        length = 4
        start_date = str(days.index[-length])[:10]
        end_date = str(end_date)[:10]
        date = [start_date, end_date]

        # Params
        env_params['initial_amount'] = initial_amount
        env_params['initial_allocation'] = [initial_allocation_1, initial_allocation_2]
        env_params['commission_perc'] = commission_perc

        # Run
        run(
            data_params,
            env_params,
            model_params['model_name'],
            date,
        )
    


if __name__ == '__main__':
    main()
