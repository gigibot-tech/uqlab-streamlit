import gc
from typing import Union, Callable

import numpy as np
import keras.backend as K
from keras.layers import Dense
from keras.src.callbacks import CSVLogger
from keras_uncertainty.models import StochasticClassifier
from sklearn.metrics import accuracy_score

from walaris.disentanglement_paper.datatypes import Dataset
from walaris.disentanglement_paper.logging import TQDM
from walaris.disentanglement_paper.models.architectures import CustomDeepEnsembleClassifier
from walaris.disentanglement_paper.settings import BATCH_SIZE, NUM_SAMPLES, MODEL_TRAIN_VERBOSE


def entropy(probs, axis=-1, eps=1e-6):
    return -np.sum(probs * np.log(probs + eps), axis=axis)


def predictive_entropy(probs, axis=-1) -> np.ndarray:
    probs = np.mean(probs, axis=0)
    return entropy(probs, axis)


def expected_entropy(probs, eps=1e-6) -> np.ndarray:
    return -np.mean((probs * np.log(probs + eps)).sum(axis=-1), axis=0)


def mutual_information(probs) -> np.ndarray:
    return predictive_entropy(probs) - expected_entropy(probs)


def train_it_model(model_creator, x_train, y_train, n_classes, epochs) \
        -> Union[CustomDeepEnsembleClassifier, StochasticClassifier]:
    model = model_creator(n_training_samples=x_train.shape[0])

    if isinstance(model, CustomDeepEnsembleClassifier):
        for estimator in model.train_estimators:
            estimator.add(Dense(n_classes, activation="softmax"))
            estimator.compile(loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
        csv_logger = CSVLogger('./training_logs.csv', append=True, separator=';')
        model.fit(x_train, y_train, epochs=epochs, batch_size=BATCH_SIZE, verbose=MODEL_TRAIN_VERBOSE,
                  callbacks=[csv_logger])
        TQDM.update(len(model.train_estimators))
        return model

    model.add(Dense(n_classes, activation="softmax"))

    model.compile(loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"])

    csv_logger = CSVLogger('./training_logs.csv', append=True, separator=';')
    model.fit(x_train, y_train, epochs=epochs, batch_size=BATCH_SIZE, verbose=MODEL_TRAIN_VERBOSE,
              callbacks=[csv_logger])
    mc_model = StochasticClassifier(model)
    TQDM.update(1)

    return mc_model


def get_average_uncertainty_it(dataset: Dataset, architecture_func, epochs):
    if dataset.is_regression:
        return np.NaN, np.NaN, np.NaN

    n_classes = len(np.unique(dataset.y_train))
    it_model = train_it_model(architecture_func, dataset.X_train, dataset.y_train, n_classes, epochs=epochs)

    it_preds = it_model.predict_samples(dataset.X_test, num_samples=NUM_SAMPLES, batch_size=BATCH_SIZE)

    return accuracy_score(dataset.y_test, it_preds.mean(axis=0).argmax(axis=1)), \
        expected_entropy(it_preds).mean(), \
        mutual_information(it_preds).mean()


def get_ood_tprs_it(dataset: Dataset, architecture_func: Callable, epochs: int, ood_class: int):
    if dataset.is_regression:
        raise ValueError("OoD detection for regression is not implemented")

    n_classes = len(np.unique(dataset.y_train))

    it_model = train_it_model(architecture_func, dataset.X_train, dataset.y_train, n_classes, epochs=epochs)
    it_preds = it_model.predict_samples(dataset.X_test, num_samples=NUM_SAMPLES, batch_size=BATCH_SIZE)

    ale_uncertainties = expected_entropy(np.delete(it_preds, ood_class, axis=2))
    epi_uncertainties = mutual_information(np.delete(it_preds, ood_class, axis=2))

    K.clear_session()
    del it_model
    gc.collect()

    return it_preds.mean(axis=0).argmax(axis=1), ale_uncertainties, epi_uncertainties