import numpy as np
from tqdm import tqdm

from walaris.disentanglement_paper.experiment_configs import get_experiment_configs
from walaris.disentanglement_paper.settings import NUM_DEEP_ENSEMBLE_ESTIMATORS, TEST_MODE, NUM_DECREASING_DATASET_STEPS, \
    NUM_LABEL_NOISE_STEPS

number_of_models_to_train = 0
for experiment_config in get_experiment_configs():
    for model in experiment_config.models:
        for meta_experiment in experiment_config.meta_experiments:
            training_runs_per_experiment = 1
            if meta_experiment == "ood_class":
                if experiment_config.dataset:
                    training_runs_per_experiment = len(np.unique(experiment_config.dataset.y_train))
                else:
                    training_runs_per_experiment = 0
                if TEST_MODE:
                    training_runs_per_experiment = 2
            elif meta_experiment == "label_noise":
                training_runs_per_experiment = NUM_LABEL_NOISE_STEPS
            elif meta_experiment == "decreasing_dataset":
                training_runs_per_experiment = NUM_DECREASING_DATASET_STEPS
            else:
                raise ValueError(f"Unknown metaexperiment {meta_experiment}")

            if model.uq_name == "Deep Ensemble":
                number_of_models_to_train += NUM_DEEP_ENSEMBLE_ESTIMATORS * training_runs_per_experiment
            else:
                number_of_models_to_train += training_runs_per_experiment


TQDM = tqdm(total=number_of_models_to_train * 3)
