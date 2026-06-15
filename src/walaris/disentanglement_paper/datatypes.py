from dataclasses import dataclass, field
from typing import List, Callable, Iterable, Union, Optional

import numpy as np


@dataclass
class UqModel:
    model_function: Callable
    uq_name: str
    epochs: int


@dataclass
class Dataset:
    X_train: np.ndarray
    y_train: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    is_regression: field(default=False)


@dataclass
class ExperimentConfig:
    dataset_name: str
    dataset: Optional[Dataset]
    models: List[UqModel]
    meta_experiments: List[str]


# This is used for plotting accuracy, aleatoric and epistemic uncertainty while changing a certain parameter.
# For the decreasing dataset experiment, the changed parameter is different sizes of the training data.
@dataclass
class UncertaintyResults:
    accuracies: Union[List, Iterable] = field(default_factory=lambda: [])
    aleatoric_uncertainties: List = field(default_factory=lambda: [])
    epistemic_uncertainties: List = field(default_factory=lambda: [])
    changed_parameter_values: Union[List, Iterable] = field(default_factory=lambda: [])

    def append_values(self, accuracy, aleatoric_uncertainty, epistemic_uncertainty, parameter):
        self.accuracies.append(accuracy)
        self.aleatoric_uncertainties.append(aleatoric_uncertainty)
        self.epistemic_uncertainties.append(epistemic_uncertainty)
        self.changed_parameter_values.append(parameter)
