from typing import Callable
import gc
import keras.backend as K


import numpy as np
from keras_uncertainty.models import DeepEnsembleRegressor, DeepEnsembleClassifier, DisentangledStochasticClassifier, \
    TwoHeadStochasticRegressor
from keras_uncertainty.models.disentangling import sampling_softmax
from sklearn.metrics import accuracy_score

from uqlab.disentanglement_paper.datatypes import Dataset
from uqlab.disentanglement_paper.models.gaussian_logits_models import train_gaussian_logits_model, uncertainty
from uqlab.disentanglement_paper.settings import NUM_SAMPLES, BATCH_SIZE


def softmax(x, axis=-1):
    x = x - np.max(x, axis=axis, keepdims=True)

    return np.exp(x) / np.sum(np.exp(x), axis=axis, keepdims=True)


class LogitVarianceDisentangledStochasticClassifier(DisentangledStochasticClassifier):
    def __init__(self, parent_classifier, epi_num_smaples=10, ale_num_samples=100):
        super(LogitVarianceDisentangledStochasticClassifier, self).__init__(parent_classifier.model, epi_num_smaples, ale_num_samples)

    def predict(self, inp, num_samples=None, batch_size=32):
        y_logits_mean, y_logits_std_ale, y_logits_std_epi = TwoHeadStochasticRegressor.predict(self, inp,
                                                                                               num_samples=num_samples,
                                                                                               batch_size=batch_size,
                                                                                               disentangle_uncertainty=True)

        y_probs = sampling_softmax(y_logits_mean, y_logits_std_ale + y_logits_std_epi, num_samples=self.ale_num_samples)
        return y_probs, y_logits_std_ale, y_logits_std_epi


def get_average_uncertainty_logit_variance(dataset: Dataset, architecture_func, epochs):
    n_classes = len(np.unique(dataset.y_train))
    regression = dataset.is_regression

    if regression:
        return np.NaN, np.NaN, np.NaN

    gaussian_logits_model = train_gaussian_logits_model(architecture_func, dataset.X_train, dataset.y_train, n_classes,
                                                        epochs=epochs, regression=regression)
    gaussian_logits_model = LogitVarianceDisentangledStochasticClassifier(gaussian_logits_model,
                                                                          gaussian_logits_model.epi_num_samples,
                                                                          gaussian_logits_model.ale_num_samples)
    if isinstance(gaussian_logits_model, DeepEnsembleRegressor):
        num_samples = gaussian_logits_model.num_estimators
    elif isinstance(gaussian_logits_model.model, DeepEnsembleClassifier):
        num_samples = gaussian_logits_model.model.num_estimators
    else:
        num_samples = NUM_SAMPLES

    pred_mean, pred_ale_std, pred_epi_std = gaussian_logits_model.predict(dataset.X_test, batch_size=BATCH_SIZE,
                                                                          num_samples=num_samples)
    score = accuracy_score(dataset.y_test, pred_mean.argmax(axis=1))

    return score, pred_ale_std.mean(), pred_epi_std.mean()


def get_ood_tprs_logit_variance(dataset: Dataset, architecture_func: Callable, epochs: int, ood_class: int):
    if dataset.is_regression:
        return np.zeros_like(dataset.X_test), np.zeros_like(dataset.X_test), np.zeros_like(dataset.X_test)

    n_classes = len(np.unique(dataset.y_train))
    gaussian_logits_model = train_gaussian_logits_model(architecture_func, dataset.X_train, dataset.y_train, n_classes,
                                                        epochs=epochs)
    gaussian_logits_model = LogitVarianceDisentangledStochasticClassifier(gaussian_logits_model,
                                                                          gaussian_logits_model.epi_num_samples,
                                                                          gaussian_logits_model.ale_num_samples)
    if isinstance(gaussian_logits_model.model, DeepEnsembleClassifier):
        num_samples = gaussian_logits_model.model.num_estimators
    else:
        num_samples = NUM_SAMPLES

    pred_mean, pred_ale_std, pred_epi_std = gaussian_logits_model.predict(dataset.X_test, batch_size=BATCH_SIZE,
                                                                          num_samples=num_samples)

    ale_uncertainties = uncertainty(np.delete(pred_ale_std, ood_class, axis=1))
    epi_uncertainties = uncertainty(np.delete(pred_epi_std, ood_class, axis=1))

    K.clear_session()
    gc.collect()

    return pred_mean.argmax(axis=1), ale_uncertainties, epi_uncertainties