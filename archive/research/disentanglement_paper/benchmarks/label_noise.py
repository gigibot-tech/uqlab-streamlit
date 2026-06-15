import gc
import os
from datetime import datetime

import numpy as np
from matplotlib import pyplot as plt
from sklearn.utils import shuffle

from uqlab.disentanglement_paper.benchmarks.decreasing_dataset import request_results_or_run
from uqlab.disentanglement_paper.benchmarks.plotting import plot_results_on_idx
from uqlab.disentanglement_paper.datatypes import UncertaintyResults, ExperimentConfig, Dataset
from uqlab.disentanglement_paper.experiment_configs import get_experiment_configs
from uqlab.disentanglement_paper.logging import TQDM
from uqlab.disentanglement_paper.models.disentanglement import DISENTANGLEMENT_FUNCS
from uqlab.disentanglement_paper.settings import TEST_MODE, FIGURE_FOLDER, NUM_LABEL_NOISE_STEPS

META_EXPERIMENT_NAME = 'label_noise'


def partial_shuffle_dataset(x, y, percentage):
    x_noisy, y_noisy = shuffle(x, y)
    np.random.shuffle(y_noisy[:int(len(y_noisy) * percentage)])
    x_noisy, y_noisy = shuffle(x_noisy, y_noisy)
    return x_noisy, y_noisy


def run_label_noise(dataset: Dataset, architecture_func, epochs):
    results = {disentanglement_name: UncertaintyResults() for disentanglement_name, func in
               DISENTANGLEMENT_FUNCS.items()}

    noises = np.linspace(0, 1.0, NUM_LABEL_NOISE_STEPS)

    if TEST_MODE:
        epochs = 2

    for noise in noises:
        X_train_noisy, y_train_noisy = partial_shuffle_dataset(dataset.X_train, dataset.y_train, percentage=noise)
        X_test_noisy, y_test_noisy = partial_shuffle_dataset(dataset.X_test, dataset.y_test, percentage=noise)
        noisy_dataset = Dataset(X_train_noisy, y_train_noisy, X_test_noisy, y_test_noisy,
                                is_regression=dataset.is_regression)

        for disentanglement_name, disentanglement_func in DISENTANGLEMENT_FUNCS.items():
            results[disentanglement_name].append_values(*disentanglement_func(noisy_dataset, architecture_func,
                                                                              epochs), noise)
            gc.collect()
        gc.collect()

    return results


def label_noise(experiment_config: ExperimentConfig, from_folder=False):
    fig, axes = plt.subplots(len(DISENTANGLEMENT_FUNCS), len(experiment_config.models), figsize=(10, 6),
                             sharey=True, sharex=True)
    fontsize = 14
    plt.rcParams['font.size'] = fontsize

    accuracy_y_ax_to_share = None
    for arch_idx, architecture in enumerate(experiment_config.models):
        TQDM.set_description(
            f"Running experiment {META_EXPERIMENT_NAME} on {experiment_config.dataset_name} with {architecture.uq_name}")

        results, results_std = request_results_or_run(
            experiment_config, architecture, from_folder,
            run_function=run_label_noise, meta_experiment_name=META_EXPERIMENT_NAME)

        accuracy_y_ax_to_share = plot_results_on_idx(results, results_std, arch_idx, axes, experiment_config,
                                                     architecture,
                                                     META_EXPERIMENT_NAME, accuracy_y_ax_to_share)

    fig.tight_layout()
    if not os.path.exists(f"{FIGURE_FOLDER}/noise_dataset/"):
        os.mkdir(f"{FIGURE_FOLDER}/noise_dataset")

    if TEST_MODE:
        fig.savefig(
            f"{FIGURE_FOLDER}/noise_dataset/disentangled_uncertainties_{experiment_config.dataset_name}_TEST.pdf")
    else:
        fig.savefig(f"{FIGURE_FOLDER}/noise_dataset/disentangled_uncertainties_{experiment_config.dataset_name}.pdf")


if __name__ == "__main__":
    start_time = datetime.now()
    experiment_configs = get_experiment_configs()
    for experiment_conf in experiment_configs:
        if experiment_conf.dataset_name == "CIFAR10":
            label_noise(experiment_conf)
    print(f"Running Decreasing Dataset experiments took: {datetime.now() - start_time}")
