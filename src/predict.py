import os
import streamlit as st

from src import data, model, agent


def main(data_params, env_kwargs, model_name, date):
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
    next_allocation = df_actions_ppo * env_kwargs['initial_amount']

    return next_allocation

    # Account value calculation
    ppo_cumprod = (df_daily_return_ppo.daily_return + 1).cumprod() - 1
    account_value = env_kwargs['initial_amount'] + (env_kwargs['initial_amount'] * ppo_cumprod)

    # st.write('Account value')
    # st.dataframe(account_value)

    # return account_value.iat[-1], df_actions_ppo.iloc[-1, :].values.flatten().tolist()
