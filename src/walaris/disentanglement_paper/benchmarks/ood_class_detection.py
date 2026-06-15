import os
from datetime import datetime
from typing import Dict

import numpy as np
from matplotlib import pyplot as plt
from sklearn.metrics import roc_curve, accuracy_score, auc

from walaris.disentanglement_paper.benchmarks.decreasing_dataset import request_results_or_run
from walaris.disentanglement_paper.datatypes import UncertaintyResults, Dataset
from walaris.disentanglement_paper.experiment_configs import get_experiment_configs
from walaris.disentanglement_paper.logging import TQDM
from walaris.disentanglement_paper.models.disentanglement import DISENTANGLEMENT_FUNCS
from walaris.disentanglement_paper.models.gaussian_logits_models import get_ood_tprs_gaussian_logits
from walaris.disentanglement_paper.models.information_theoretic_models import get_ood_tprs_it
from walaris.disentanglement_paper.models.logit_variance import get_ood_tprs_logit_variance
from walaris.disentanglement_paper.settings import TEST_MODE, FIGURE_FOLDER

META_EXPERIMENT_NAME = "ood_class"


def determine_tprs_for_roc(base_fpr, y_ood_true, y_ood_score):
    fpr, tpr, _ = roc_curve(y_ood_true, y_ood_score)
    tpr = np.interp(base_fpr, fpr, tpr)
    tpr[0] = 0.0
    return tpr


def get_ood_disentanglement_tprs_func(disentanglement_name):
    match disentanglement_name:
        case "gaussian_logits":
            return get_ood_tprs_gaussian_logits
        case "it":
            return get_ood_tprs_it
        case "logit_variance":
            return get_ood_tprs_logit_variance
        case _:
            raise ValueError(f"No OoD Disentanglement func known for {disentanglement_name}")


def run_ood_class_detection(dataset, architecture_func, epochs) -> Dict[str, UncertaintyResults]:
    ood_classes = np.unique(dataset.y_train)
    y_test = dataset.y_test.reshape(-1)
    y_train = dataset.y_train.reshape(-1)

    base_fpr = np.linspace(0, 1, 101)

    if TEST_MODE:
        epochs = 1
        ood_classes = ood_classes[:2]

    results = {disentanglement_name: UncertaintyResults() for disentanglement_name, func in
               DISENTANGLEMENT_FUNCS.items()}
    for disentanglement_name, _ in DISENTANGLEMENT_FUNCS.items():
        ale_tprs = []
        epi_tprs = []
        accuracies = []
        for ood_class in ood_classes:
            X_train_id = dataset.X_train[y_train != ood_class]
            y_train_id = dataset.y_train[y_train != ood_class]
            y_test_ood = y_test == ood_class
            ood_dataset = Dataset(X_train_id, y_train_id, dataset.X_test, y_test_ood,
                                  is_regression=dataset.is_regression)

            ood_disentanglement_tprs_func = get_ood_disentanglement_tprs_func(disentanglement_name)  # TODO

            preds, ale_uncertainties, epi_uncertainties = ood_disentanglement_tprs_func(ood_dataset, architecture_func,
                                                                                        epochs, ood_class)
            ale_tprs.append(determine_tprs_for_roc(base_fpr, y_test_ood, ale_uncertainties))
            epi_tprs.append(determine_tprs_for_roc(base_fpr, y_test_ood, epi_uncertainties))

            # Sanity check
            accuracy = accuracy_score(y_test[y_test != ood_class], preds[y_test != ood_class])
            accuracies.append(accuracy)
        results[disentanglement_name] = UncertaintyResults(accuracies=np.ones_like(base_fpr) * np.mean(accuracies),
                                                           aleatoric_uncertainties=np.array(ale_tprs).mean(axis=0),
                                                           epistemic_uncertainties=np.array(epi_tprs).mean(axis=0),
                                                           changed_parameter_values=base_fpr)

    return results


def plot_roc_on_ax(ax, aleatoric_tpr, epistemic_tpr, base_fpr, std=None):
    ax.plot(base_fpr, aleatoric_tpr, label="Aleatoric")
    ax.plot(base_fpr, epistemic_tpr, label="Epistemic")
    ax.plot(base_fpr, base_fpr, color='black', linestyle='dashed')

    if std:
        ale_auc = auc(base_fpr, aleatoric_tpr)
        epi_auc = auc(base_fpr, epistemic_tpr)

        ale_auc_std = auc(base_fpr, np.add(std.aleatoric_uncertainties, aleatoric_tpr)) - ale_auc
        epi_auc_std = auc(base_fpr, np.add(std.epistemic_uncertainties, epistemic_tpr)) - epi_auc
        return ale_auc, epi_auc, ale_auc_std, epi_auc_std

    return auc(base_fpr, aleatoric_tpr), auc(base_fpr, epistemic_tpr), 0.0, 0.0


def plot_ood_class_detection(experiment_config, from_folder=None):
    if not os.path.exists(f"{FIGURE_FOLDER}/ood_class/"):
        os.mkdir(f"{FIGURE_FOLDER}/ood_class/")

    fig, axes = plt.subplots(len(DISENTANGLEMENT_FUNCS), len(experiment_config.models), figsize=(10, 6), sharey=True,
                             sharex=True)

    for arch_idx, architecture in enumerate(experiment_config.models):
        TQDM.set_description(
            f"Running experiment {META_EXPERIMENT_NAME} on {experiment_config.dataset_name} with {architecture.uq_name}")

        results, results_std = request_results_or_run(
            experiment_config, architecture, from_folder, run_ood_class_detection, META_EXPERIMENT_NAME)

        for disentanglement_idx, (disentanglement_name, disentanglement_results) in enumerate(results.items()):
            if results_std:
                disentanglement_results_std = results_std[disentanglement_name]
            else:
                disentanglement_results_std = None
            ale_auc, epi_auc, ale_auc_std, epi_auc_std = plot_roc_on_ax(axes[disentanglement_idx][arch_idx],
                                                                        disentanglement_results.aleatoric_uncertainties,
                                                                        disentanglement_results.epistemic_uncertainties,
                                                                        disentanglement_results.changed_parameter_values,
                                                                        std=disentanglement_results_std)
            print(f"OOD AUROC {architecture.uq_name}, {disentanglement_name}")
            print(f"Ale {ale_auc:.3} \pm {ale_auc_std:.4}\t\t Epi {epi_auc:.3} \pm {epi_auc_std:.4}")
            if arch_idx == 0:
                axes[disentanglement_idx][arch_idx].set_ylabel(f"{disentanglement_name}\nTrue Positive Rate")

            axes[disentanglement_idx][arch_idx].set_title(architecture.uq_name)
            axes[disentanglement_idx][arch_idx].set_xlabel("False Positive Rate")

        if arch_idx == len(experiment_config.models) - 1:
            axes[0][arch_idx].legend(loc="lower right")

    fig.tight_layout()

    if TEST_MODE:
        fig.savefig(f"{FIGURE_FOLDER}/ood_class/ood_roc_curve_{experiment_config.dataset_name}_TEST.pdf")
    else:
        fig.savefig(f"{FIGURE_FOLDER}/ood_class/ood_roc_curve_{experiment_config.dataset_name}.pdf")


if __name__ == "__main__":
    start_time = datetime.now()

    experiment_configs = get_experiment_configs()
    for experiment_conf in experiment_configs:
        if experiment_conf.dataset_name == "CIFAR10":
            plot_ood_class_detection(experiment_conf)
    print(f"Running Decreasing Dataset experiments took: {datetime.now() - start_time}")
