from typing import Dict

import numpy as np
from keras import backend as K
from uqlab.disentanglement_paper.datatypes import UncertaintyResults


def normalise(x):
    x = np.array(x)
    return (x - min(x)) / max(x - min(x))


def print_correlations(results: Dict[str, UncertaintyResults]):
    for disentanglement_name, disentanglement_results in results.items():
        if not disentanglement_results.aleatoric_uncertainties:
            ale_corr = -1.0
            epi_corr = -1.0
        else:
            ale_corr = np.corrcoef(np.array(disentanglement_results.aleatoric_uncertainties),
                                   disentanglement_results.accuracies)[0, 1]
            epi_corr = np.corrcoef(np.array(disentanglement_results.epistemic_uncertainties),
                                   disentanglement_results.accuracies)[0, 1]

        print(f"{disentanglement_name} Ale corr \t {disentanglement_name} Epi corr")
        print(f"{ale_corr:.3} \t & \t {epi_corr:.3}")


def custom_regression_gaussian_nll_loss(y_true, mean, variance):
    epsilon = 1e-8

    return 0.5 * K.mean(K.log(variance + epsilon) + K.square(y_true - mean) / (variance + epsilon))
