import os
from typing import Tuple, Dict

import pandas as pd

from walaris.disentanglement_paper.data.eeg import N_EEG_SUBJECTS
from walaris.disentanglement_paper.datatypes import UncertaintyResults
from walaris.disentanglement_paper.models.disentanglement import DISENTANGLEMENT_FUNCS
from walaris.disentanglement_paper.settings import TEST_MODE, DATA_FOLDER, N_REPETITIONS


def get_test_append():
    if TEST_MODE:
        test_append = "_test"
    else:
        test_append = ""

    return test_append


def load_and_combine_multiple_logs(experiment_config, architecture, meta_experiment_name, n_logs) -> \
        Tuple[Dict[str, UncertaintyResults], Dict[str, UncertaintyResults]]:
    results = {}
    results_std = {}
    for disentanglement_name, _ in DISENTANGLEMENT_FUNCS.items():
        dfs = []
        for log_id in range(n_logs):
            try:
                dfs.append(pd.read_csv(f"{DATA_FOLDER}/{meta_experiment_name}/{meta_experiment_name}_"
                                       f"{experiment_config.dataset_name} {log_id}_{architecture.uq_name}_"
                                       f"{disentanglement_name}_results{get_test_append()}.csv"))
            except FileNotFoundError:
                print(
                    f"Failed to find data for log {meta_experiment_name}_{experiment_config.dataset_name} "
                    f"{log_id}_{architecture.uq_name}_"
                    f"{disentanglement_name}. Skipping...")
        try:
            df = pd.concat(dfs)
            df_std = df.groupby(df.index).sem()
            df = df.groupby(df.index).mean()
        except (TypeError, ValueError):
            results[disentanglement_name] = None
            results_std[disentanglement_name] = None
            raise ValueError(f"There are no logs available for {meta_experiment_name} {experiment_config.dataset_name} {architecture.uq_name} {disentanglement_name}.")

        results[disentanglement_name] = UncertaintyResults(**df.to_dict(orient='list'))
        results_std[disentanglement_name] = UncertaintyResults(**df_std.to_dict(orient='list'))

    return results, results_std


def save_results_to_file(experiment_config, architecture, results: Dict[str, UncertaintyResults], meta_experiment_name):
    if not os.path.exists(f"{DATA_FOLDER}/"):
        os.mkdir(f"{DATA_FOLDER}/")
    if not os.path.exists(f"{DATA_FOLDER}/{meta_experiment_name}/"):
        os.mkdir(f"{DATA_FOLDER}/{meta_experiment_name}/")

    for disentanglement_name, disentanglement_results in results.items():
        df = pd.DataFrame(disentanglement_results.__dict__)
        df.to_csv(f"{DATA_FOLDER}/{meta_experiment_name}/{meta_experiment_name}_"
                  f"{experiment_config.dataset_name}_{architecture.uq_name}_"
                  f"{disentanglement_name}_results{get_test_append()}.csv", index=False)


def load_results_from_file(experiment_config, architecture, meta_experiment_name):
    if experiment_config.dataset_name == "Motor Imagery BCI":
        return load_and_combine_multiple_logs(experiment_config, architecture, meta_experiment_name,
                                              n_logs=N_EEG_SUBJECTS)

    if not experiment_config.dataset:
        return load_and_combine_multiple_logs(experiment_config, architecture, meta_experiment_name,
                                              n_logs=N_REPETITIONS)

    results = {}
    for disentanglement_name, _ in DISENTANGLEMENT_FUNCS.items():
        df = pd.read_csv(f"{DATA_FOLDER}/{meta_experiment_name}/{meta_experiment_name}_"
                         f"{experiment_config.dataset_name}_{architecture.uq_name}_"
                         f"{disentanglement_name}_results{get_test_append()}.csv")
        disentanglement_results = UncertaintyResults(**df.to_dict(orient='list'))
        results[disentanglement_name] = disentanglement_results

    return results, None
