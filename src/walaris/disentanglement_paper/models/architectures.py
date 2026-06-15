from typing import Callable

import numpy as np
from keras import Input, Model
from keras.src.layers import Dense, Dropout
from keras_uncertainty.layers import StochasticDropout, DropConnectDense, FlipoutDense
from keras_uncertainty.models import DeepEnsembleClassifier, DeepEnsembleRegressor

from walaris.disentanglement_paper.models.backbones import get_cifar10_convolutional_blocks, get_eeg_convolutional_blocks, \
    get_fashion_mnist_convolutional_blocks, get_wine_backbone, get_auto_mpg_backbone, \
    get_utkface_convolutional_blocks, get_blobs_backbone
from walaris.disentanglement_paper.settings import NUM_DEEP_ENSEMBLE_ESTIMATORS
from walaris.disentanglement_paper.util import custom_regression_gaussian_nll_loss


def get_architecture(dataset_name: str, bnn_name: str, is_regression=False) -> Callable:
    match dataset_name:
        case "CIFAR10":
            backbone_func = get_cifar10_convolutional_blocks
            hidden_size = 64
        case "Motor Imagery BCI":
            backbone_func = get_eeg_convolutional_blocks
            hidden_size = 32
        case "blobs":
            backbone_func = get_blobs_backbone
            hidden_size = 32
        case "Fashion MNIST":
            backbone_func = get_fashion_mnist_convolutional_blocks
            hidden_size = 64
        case "Wine":
            backbone_func = get_wine_backbone
            hidden_size = 16
        case "AutoMPG":
            backbone_func = get_auto_mpg_backbone
            hidden_size = 16
        case "UTKFace":
            backbone_func = get_utkface_convolutional_blocks
            hidden_size = 256
        case _:
            raise ValueError(f"No architecture implemented for {dataset_name}")

    match bnn_name:
        case "MC-Dropout":
            bnn_func = get_dropout_from_backbone
        case "MC-DropConnect":
            bnn_func = get_dropconnect_from_backbone
        case "Deep Ensemble":
            if is_regression:
                bnn_func = get_regression_ensemble_from_backbone
            else:
                bnn_func = get_ensemble_from_backbone
        case "Flipout":
            bnn_func = get_flipout_from_backbone
        case _:
            raise ValueError(f"No BNN implemented for {bnn_name}")

    def bnn_constructor(n_training_samples):
        return bnn_func(backbone_func, hidden_size=hidden_size, n_training_samples=n_training_samples)

    return bnn_constructor


class CustomDeepEnsembleClassifier(DeepEnsembleClassifier):
    def __init__(self, model_fn, num_estimators):
        super(CustomDeepEnsembleClassifier, self).__init__(model_fn, num_estimators)
        self.estimator_to_use = 0

    def predict_samples(self, x, num_samples=-1, batch_size=-1):
        predictions = []
        for estimator in self.test_estimators:
            predictions.append(estimator.predict(x, batch_size=batch_size, verbose=0))
        return np.array(predictions)

    def predict(self, X, batch_size=32, num_ensembles=None, return_std=False, **kwargs):
        if "verbose" not in kwargs:
            kwargs["verbose"] = 0

        prediction = self.test_estimators[self.estimator_to_use % self.num_estimators].predict(X, batch_size=batch_size,
                                                                                               **kwargs)
        self.estimator_to_use += 1

        return prediction


def get_dropout_from_backbone(backbone_func, prob=0.3, hidden_size=64, **_):
    model = backbone_func()
    model.add(Dense(hidden_size, activation='relu'))
    model.add(StochasticDropout(prob))

    return model


def get_ensemble_from_backbone(backbone_func, prob=0.3, hidden_size=64, **_):
    def model_fn():
        model = backbone_func()
        model.add(Dense(hidden_size, activation='relu'))
        model.add(Dropout(prob))

        model.compile(loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"])

        return model

    ensemble_model = CustomDeepEnsembleClassifier(model_fn, num_estimators=NUM_DEEP_ENSEMBLE_ESTIMATORS)
    return ensemble_model


def get_regression_ensemble_from_backbone(backbone_func, prob=0.3, hidden_size=64, **_):
    def model_fn():
        backbone = backbone_func()
        hidden_representation = backbone(backbone.inputs)
        mean = Dense(1, activation="linear")(hidden_representation)
        var = Dense(1, activation="softplus")(hidden_representation)

        label_layer = Input((1,))

        train_model = Model([backbone.inputs, label_layer], [mean, var], name="train_model")
        pred_model = Model(backbone.inputs, [mean, var], name="pred_model")

        loss = custom_regression_gaussian_nll_loss(label_layer, mean, var)
        train_model.add_loss(loss)

        train_model.compile(optimizer="adam")

        return train_model, pred_model

    ensemble_model = DeepEnsembleRegressor(model_fn, num_estimators=NUM_DEEP_ENSEMBLE_ESTIMATORS)
    return ensemble_model


def get_flipout_from_backbone(backbone_func, n_training_samples, hidden_size=64, **_):
    num_batches = n_training_samples / 32
    kl_weight = 1.0 / num_batches
    prior_params = {
        'prior_sigma_1': 5.0,
        'prior_sigma_2': 2.0,
        'prior_pi': 0.5
    }

    model = backbone_func()
    model.add(FlipoutDense(hidden_size, kl_weight, **prior_params, activation="relu", ))

    return model


def get_dropconnect_from_backbone(backbone_func, hidden_size=64, prob=0.3, **_):
    model = backbone_func()
    model.add(DropConnectDense(hidden_size, activation='relu', prob=prob))

    return model
