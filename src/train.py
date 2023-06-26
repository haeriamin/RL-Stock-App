import os
from stable_baselines3 import PPO

from src import params, data, model, agent


def main(data_params, env_kwargs, model_params, train_params, model_name, date):
    # Get training data
    df = data.main(
        stocks = data_params['stocks'],
        date = date,
        # mode = 'train',
    )

    # Create environment
    train_env = model.StockPortfolioEnv(
        df = df,
        **env_kwargs)
    
    env_train, _ = train_env.get_sb_env()

    # Define PPO agent
    my_agent = agent.Agent(
        env = env_train,
    )

    # model_ppo = my_agent.get_model(
    #     model_name = model_name,
    #     model_kwargs = model_params,
    # )

    model_ppo = PPO.load(
        os.path.join('src', model_name),
        env=env_train,
        # **model_params,
    )

    trained_ppo = my_agent.train(
        model = model_ppo,
        train_kwargs = train_params 
    )

    trained_ppo.save(os.path.join('src', model_name))
