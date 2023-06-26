import os

from src import params, data, model, agent


def main(load_data, load_model):
    if not load_model:
        # Get params
        data_params, env_kwargs, model_params, train_params = params.main()

        # Get training data
        df = data.main(
            stocks = data_params['stocks'],
            mode = 'train',
            load = load_data,
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
        model_ppo = my_agent.get_model(
            model_kwargs = model_params,
        )
        trained_ppo = my_agent.train(
            model = model_ppo,
            train_kwargs = train_params 
        )
        trained_ppo.save(
            os.path.join(config.TRAINED_MODEL_DIR, model_params['model_name']))
    else:
        pass

