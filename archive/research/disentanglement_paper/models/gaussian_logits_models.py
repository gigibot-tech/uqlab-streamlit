import gc
from typing import Union, Callable

import numpy as np
from keras.layers import Dense, Input
from keras.models import Model
from keras.src.callbacks import CSVLogger
from keras_uncertainty.layers import SamplingSoftmax
from keras_uncertainty.models import DisentangledStochasticClassifier, DeepEnsembleClassifier, \
    TwoHeadStochasticRegressor, DeepEnsembleRegressor
from keras_uncertainty.utils import numpy_entropy
from sklearn.metrics import accuracy_score, mean_squared_error

from uqlab.disentanglement_paper.datatypes import Dataset
from uqlab.disentanglement_paper.logging import TQDM
from uqlab.disentanglement_paper.settings import BATCH_SIZE, NUM_SAMPLES, MODEL_TRAIN_VERBOSE
from uqlab.disentanglement_paper.util import custom_regression_gaussian_nll_loss
import keras.backend as K


def uncertainty(probs):
    return numpy_entropy(probs, axis=-1)


def two_head_model(trunk_model, num_classes=2, num_samples=100):
    input_shape = trunk_model.layers[0].input.shape[1:]

    inp = Input(shape=input_shape)
    x = trunk_model(inp)
    logit_mean = Dense(num_classes, activation="linear")(x)
    logit_var = Dense(num_classes, activation="softplus")(x)
    probs = SamplingSoftmax(num_samples=num_samples, variance_type="linear_std")([logit_mean, logit_var])

    train_model = Model(inp, probs, name="train_model")
    pred_model = Model(inp, [logit_mean, logit_var], name="pred_model")

    train_model.compile(loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"])

    return train_model, pred_model


def two_head_regression_model(trunk_model, num_samples=100):
    input_shape = trunk_model.layers[0].input.shape[1:]

    inp = Input(shape=input_shape)
    x = trunk_model(inp)
    mean = Dense(1, activation="linear")(x)
    var = Dense(1, activation="softplus")(x)
    label_layer = Input((1,))

    train_model = Model([inp, label_layer], [mean, var], name="train_model")
    pred_model = Model(inp, [mean, var], name="pred_model")

    loss = custom_regression_gaussian_nll_loss(label_layer, mean, var)
    train_model.add_loss(loss)

    train_model.compile(optimizer="adam", metrics=["mse"])
    return train_model, pred_model


def train_gl_deep_ensemble_classifier(trunk_model, x_train, y_train, n_classes, epochs):
    for i, estimator in enumerate(trunk_model.train_estimators):
        train_model, pred_model = two_head_model(estimator, n_classes)
        csv_logger = CSVLogger('./training_logs.csv', append=True, separator=';')
        train_model.fit(x_train, y_train, epochs=epochs, batch_size=BATCH_SIZE, verbose=MODEL_TRAIN_VERBOSE,
                        callbacks=[csv_logger])
        trunk_model.test_estimators[i] = pred_model
        TQDM.update(1)
        gc.collect()
    trunk_model.outputs = [0, 1]  # This tells Stochastic Model that there's two outputs
    return DisentangledStochasticClassifier(trunk_model, epi_num_samples=trunk_model.num_estimators)


def train_gl_deep_ensemble_regression(trunk_model, x_train, y_train, epochs):
    csv_logger = CSVLogger('./training_logs.csv', append=True, separator=';')
    trunk_model.fit([x_train, y_train], np.empty_like(y_train), epochs=epochs, batch_size=BATCH_SIZE,
                    verbose=MODEL_TRAIN_VERBOSE, callbacks=[csv_logger])
    TQDM.update(len(trunk_model.train_estimators))
    gc.collect()
    return trunk_model


def train_gaussian_logits_model(trunk_model_creator, x_train, y_train, n_classes, epochs,
                                regression=False) -> \
        Union[DisentangledStochasticClassifier, TwoHeadStochasticRegressor, DeepEnsembleRegressor]:
    trunk_model = trunk_model_creator(n_training_samples=x_train.shape[0])

    if isinstance(trunk_model, DeepEnsembleClassifier):
        return train_gl_deep_ensemble_classifier(trunk_model, x_train, y_train, n_classes, epochs)
    elif isinstance(trunk_model, DeepEnsembleRegressor):
        return train_gl_deep_ensemble_regression(trunk_model, x_train, y_train, epochs)

    if regression:
        train_model, pred_model = two_head_regression_model(trunk_model)
    else:
        train_model, pred_model = two_head_model(trunk_model, n_classes)

    csv_logger = CSVLogger('./training_logs.csv', append=True, separator=';')

    batch_size = BATCH_SIZE
    if batch_size > len(y_train):
        batch_size = len(y_train)

    if regression:
        train_model.fit([x_train, y_train], np.empty_like(y_train), epochs=epochs, batch_size=batch_size,
                        verbose=MODEL_TRAIN_VERBOSE, callbacks=[csv_logger])
        final_model = TwoHeadStochasticRegressor(pred_model, variance_type="linear_std")
    else:
        train_model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size, verbose=MODEL_TRAIN_VERBOSE,
                        callbacks=[csv_logger])
        final_model = DisentangledStochasticClassifier(pred_model, epi_num_samples=NUM_SAMPLES)
    TQDM.update(1)

    return final_model


def get_average_uncertainty_gaussian_logits(dataset: Dataset, architecture_func, epochs):
    n_classes = len(np.unique(dataset.y_train))
    regression = dataset.is_regression
    gaussian_logits_model = train_gaussian_logits_model(architecture_func, dataset.X_train, dataset.y_train, n_classes,
                                                        epochs=epochs, regression=regression)

    if isinstance(gaussian_logits_model, DeepEnsembleRegressor):
        num_samples = gaussian_logits_model.num_estimators
    elif isinstance(gaussian_logits_model.model, DeepEnsembleClassifier):
        num_samples = gaussian_logits_model.model.num_estimators
    else:
        num_samples = NUM_SAMPLES

    if regression:
        pred_mean, pred_ale_std, pred_epi_std = gaussian_logits_model.predict(dataset.X_test,
                                                                              disentangle_uncertainty=True)
        score = mean_squared_error(dataset.y_test, pred_mean)

        return (score,
                pred_ale_std.mean(),
                pred_epi_std.mean())
    else:
        pred_mean, pred_ale_std, pred_epi_std = gaussian_logits_model.predict(dataset.X_test, batch_size=BATCH_SIZE,
                                                                              num_samples=num_samples)
        score = accuracy_score(dataset.y_test, pred_mean.argmax(axis=1))
        del gaussian_logits_model
        K.clear_session()
        gc.collect()
        return (score,
                uncertainty(pred_ale_std).mean(),
                uncertainty(pred_epi_std).mean())


def get_ood_tprs_gaussian_logits(dataset: Dataset, architecture_func: Callable, epochs: int, ood_class: int):
    if dataset.is_regression:
        raise ValueError("OoD detection for regression is not implemented")

    n_classes = len(np.unique(dataset.y_train))

    gaussian_logits_model = train_gaussian_logits_model(architecture_func, dataset.X_train, dataset.y_train,
                                                        n_classes, epochs=epochs)

    if isinstance(gaussian_logits_model.model, DeepEnsembleClassifier):
        num_samples = gaussian_logits_model.model.num_estimators
    else:
        num_samples = NUM_SAMPLES

    pred_mean, pred_ale_std, pred_epi_std = gaussian_logits_model.predict(dataset.X_test, batch_size=BATCH_SIZE,
                                                                          num_samples=num_samples)

    ale_uncertainties = uncertainty(np.delete(pred_ale_std, ood_class, axis=1))
    epi_uncertainties = uncertainty(np.delete(pred_epi_std, ood_class, axis=1))

    del gaussian_logits_model
    K.clear_session()
    gc.collect()

    return pred_mean.argmax(axis=1), ale_uncertainties, epi_uncertainties