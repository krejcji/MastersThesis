import sys
import os
import time
from pathlib import Path
from functools import partial

import optuna
import yaml
from dehb import DEHB
from smac import HyperparameterOptimizationFacade, MultiFidelityFacade, Scenario
from smac.intensifier.hyperband import Hyperband
from ConfigSpace import ConfigurationSpace, Float, Integer, Categorical

from load_data import load_data
from train_net import train_net
from logger import Logger
from logger import BudgetExceededException

EXP_NAME = "mnist_simple" # Default experiment name if not provided in command line

# Implemented optimizers - Optuna (+RS, HB), SMAC (+BOHB), DEHB

# Optuna objective function
def objective_optuna(trial, trainloader=None, valloader=None, config=None, logger=None):
    # Suggest new parameter values
    params = parse_fixed_params(config)
    for param in config['tunable_params']:
        name = param['name']
        if param['type'] == 'float':
            params[name] = trial.suggest_float(param['name'], param['low'], param['high'], log=param['log'])
        elif param['type'] == 'int':
            params[name] = trial.suggest_int(param['name'], param['low'], param['high'])
        elif param['type'] == 'categorical':
            params[name] = trial.suggest_categorical(param['name'], param['choices'])
        else:
            raise ValueError(f"Unknown parameter type: {param['type']}")

    '''
    from torch.profiler import profile, record_function, ProfilerActivity
    with profile(activities=[ProfilerActivity.CPU], record_shapes=True, use_cuda=False) as prof:
        loss = train_net(trainloader, valloader, params, config, trial)
    print(prof.key_averages().table(sort_by="self_cpu_time_total"))
    '''
    loss = train_net(trainloader, valloader, params, config, trial=trial, logger=logger)

    return loss

def optimize_optuna(config, trainloader, valloader, logger, repeat=0):
    # Prepare database
    if not os.path.exists(f"experiments/{exp_name}/outputs"):
        os.makedirs(f"experiments/{exp_name}/outputs")

    # The database must not exists, or Optuna would throw an exception
    db_str = f"experiments/{exp_name}/outputs/{exp_name}_{repeat}.db"
    db_path = Path(db_str)
    if db_path.exists():
        db_path.unlink()

    storage_url = f"sqlite:///{db_str}"

    study = optuna.create_study(storage=storage_url, direction='minimize', load_if_exists=False, study_name=exp_name)
    study.optimize(lambda trial: objective_optuna(trial, trainloader=trainloader, valloader=valloader, config=config,logger=logger))

def optimize_rs(config, trainloader, valloader, logger):
    # Prepare database
    if not os.path.exists(f"experiments/{exp_name}/outputs"):
        os.makedirs(f"experiments/{exp_name}/outputs")
    storage_url = f"sqlite:///experiments/{exp_name}/outputs/{exp_name}.db"

    study = optuna.create_study(storage=storage_url, direction='minimize', load_if_exists=True, study_name=exp_name)
    study.sampler = optuna.samplers.RandomSampler(seed=seed)
    study.pruner = optuna.pruners.NopPruner()
    study.optimize(lambda trial: objective_optuna(trial, trainloader=trainloader, valloader=valloader, config=config, logger=logger),
                    n_trials=config['hp_optimizer']['budget'])

# SMAC objective function
def objective_smac(config, seed: int=0, trainloader=None, valloader=None, configuration=None, budget=None, logger=None):
    params = dict(config)
    for param in configuration['fixed_params']:
        params[param['name']] = param['value']

    # Internal budget allocated by SMAC
    if budget is not None:
        params['epochs'] = int(budget)

    loss = train_net(trainloader, valloader, params, configuration, logger=logger)

    return loss

def optimize_smac(config, trainloader, valloader, logger, budget = None):
    configspace = ConfigurationSpace()
    for param in config['tunable_params']:
        name = param['name']
        if param['type'] == 'float':
            hp = Float(name, (param['low'], param['high']), log=param['log'])
        elif param['type'] == 'int':
            hp = Integer(name, (param['low'], param['high']))
        elif param['type'] == 'categorical':
            hp = Categorical(name, param['choices'])
        else:
            raise ValueError(f"Unknown parameter type: {param['type']}")
        configspace.add_hyperparameter(hp)

    scenario = Scenario(configspace, n_trials=config['hp_optimizer']['budget'])

    smac = HyperparameterOptimizationFacade(
        scenario,
        lambda x, seed:objective_smac(x, seed, trainloader=trainloader, valloader=valloader, configuration=config, logger=logger),
        overwrite=True,)
    incumbent = smac.optimize()

def optimize_smac_multifidelity(config, trainloader, valloader, logger, max_budget=15):
    configspace = ConfigurationSpace()
    for param in config['tunable_params']:
        name = param['name']
        if param['type'] == 'float':
            hp = Float(name, (param['low'], param['high']), log=param['log'])
        elif param['type'] == 'int':
            hp = Integer(name, (param['low'], param['high']))
        elif param['type'] == 'categorical':
            hp = Categorical(name, param['choices'])
        else:
            raise ValueError(f"Unknown parameter type: {param['type']}")
        configspace.add_hyperparameter(hp)

    scenario = Scenario(configspace,
                        walltime_limit=config['wall_time'] * 60,
                        n_trials=1000,  # Sufficiently high number not to activate
                        min_budget=1,   # TODO: Define in config
                        max_budget=max_budget,
                        n_workers=1)

    # initial_design = MFFacade.get_initial_design(scenario, n_configs=5)

    intensifier = Hyperband(scenario, incumbent_selection="highest_budget")

    obj_function = partial(objective_smac, trainloader=trainloader, valloader=valloader, configuration=config, logger=logger)

    smac = MultiFidelityFacade(
        scenario,
        obj_function,
        intensifier=intensifier,
        overwrite=True,)

    incumbent = smac.optimize()

# DEHB objective function
def objective_dehb(configuration, fidelity,  config=None, seed: int=0, trainloader=None, valloader=None, configuration_0=None, logger=None):
    params = parse_fixed_params(configuration_0)

    for param in configuration:
        params[param] = configuration[param]

    params['epochs'] = int(fidelity) if fidelity > 1 else 1
    loss = train_net(trainloader, valloader, params, configuration_0, logger=logger)

    result = {
        'fitness': loss,
        'cost': fidelity,
        'info': {}
    }

    return result

def optimize_dehb(config, trainloader, valloader, logger, max_epochs=15, budget=None):
    configspace = ConfigurationSpace()
    for param in config['tunable_params']:
        name = param['name']
        if param['type'] == 'float':
            hp = Float(name, (param['low'], param['high']), log=param['log'])
        elif param['type'] == 'int':
            hp = Integer(name, (param['low'], param['high']))
        elif param['type'] == 'categorical':
            hp = Categorical(name, param['choices'])
        else:
            raise ValueError(f"Unknown parameter type: {param['type']}")
        configspace.add_hyperparameter(hp)

    obj_function = partial(objective_dehb, config=config, seed=seed, trainloader=trainloader, valloader=valloader, configuration_0=config, logger=logger)

    dimensions = len(configspace.get_hyperparameters())
    min_fidelity = 1

    dehb = DEHB(
        f=obj_function,
        dimensions=dimensions,
        cs=configspace,
        min_fidelity=min_fidelity,
        max_fidelity=max_epochs,
        output_path='dehb_results',
        n_workers=1,
    )

    # TODO : Calculate fevals based on budget
    dehb.run(fevals=3*budget/max_epochs, verbose=True, save_intermediate=True)

def parse_fixed_params(config):
    params = dict()
    for param in config['fixed_params']:
        params[param['name']] = param['value']
    return params

if __name__ == '__main__':
    seed = 42
    # Experiment name has to be defined
    exp_name = sys.argv[1] if len(sys.argv) > 1 else EXP_NAME

    # Load the configuration file
    with open(Path('experiments') / exp_name /'config.yaml') as file:
        config = yaml.safe_load(file)

    # Set the time limits
    walltime = time.time()
    max_time = config['wall_time'] * 60 # Wall time is in minutes, convert to seconds

    # Load the data
    trainloader, valloader = load_data(config)

    for repeat in range(config['hp_optimizer']['hpo_repeats']):
        # Logging
        logging_dir = Path('experiments') / exp_name / 'outputs'
        # Logger can stop optimization if budget is exceeded
        params = parse_fixed_params(config)
        budget = config['hp_optimizer']['budget'] * params['epochs']
        logger = Logger(config, wandb=False, dir=logging_dir,budget=budget, start_time=walltime, max_time=max_time)

        try:
            # Branch on the optimizer (supported - Optuna, SMAC, DEHB)
            if config['hp_optimizer']['name'] == 'Optuna':
                optimize_optuna(config, trainloader, valloader, logger, repeat=repeat)
            elif config['hp_optimizer']['name'] == 'SMAC':
                optimize_smac(config, trainloader, valloader, logger)
            elif config['hp_optimizer']['name'] == 'SMAC_Multifidelity':
                optimize_smac_multifidelity(config, trainloader, valloader, logger, params['epochs'])
            elif config['hp_optimizer']['name'] == 'DEHB':
                optimize_dehb(config, trainloader, valloader, logger, max_epochs=params['epochs'], budget=budget)
            elif config['hp_optimizer']['name'] == 'RandomSearch':
                optimize_rs(config, trainloader, valloader, logger)
            elif config['hp_optimizer']['name'] == 'DyHPO':
                ...
            else:
                raise ValueError(f"Unknown optimizer: {config['hp_optimizer']['name']}")
        except BudgetExceededException as e:
            print(f"Budget exceeded: {e}")
            continue