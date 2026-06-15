import keras
import numpy as np
from functools import lru_cache
from walaris.disentanglement_paper.datatypes import Dataset
from walaris.disentanglement_paper.settings import TEST_MODE


@lru_cache(maxsize=None)
def get_train_test_fashion_mnist() -> Dataset:
    (x_train, y_train), (x_test, y_test) = keras.datasets.fashion_mnist.load_data()
    x_train, x_test = x_train / 255.0, x_test / 255.0
    x_train = np.expand_dims(x_train, -1)
    x_test = np.expand_dims(x_test, -1)

    if TEST_MODE:
        n_test_samples = 100
        x_test = x_test[:n_test_samples]
        y_test = y_test[:n_test_samples]

    return Dataset(x_train, y_train, x_test, y_test, is_regression=False)
