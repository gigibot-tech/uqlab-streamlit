from sklearn.datasets import make_blobs
from functools import lru_cache
from uqlab.disentanglement_paper.datatypes import Dataset

N_BLOBS_TRAINING_SAMPLES = 500


@lru_cache(maxsize=None)
def get_train_test_blobs() -> Dataset:
    X_train, y_train = make_blobs(n_samples=N_BLOBS_TRAINING_SAMPLES, n_features=2, centers=[[-1.5, 1.5], [0, -1.5]])
    X_test, y_test = make_blobs(n_samples=200, n_features=2, centers=[[-1.5, 1.5], [0, -1.5]])
    return Dataset(X_train, y_train, X_test, y_test, is_regression=False)
