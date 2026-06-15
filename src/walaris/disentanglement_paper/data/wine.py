from sklearn.datasets import load_wine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from functools import lru_cache
from walaris.disentanglement_paper.datatypes import Dataset


@lru_cache(maxsize=None)
def get_train_test_wine() -> Dataset:
    X, y = load_wine(return_X_y=True)

    le = LabelEncoder()
    y = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=0)

    sc = StandardScaler()

    X_train = sc.fit_transform(X_train)
    X_test = sc.transform(X_test)

    return Dataset(X_train, y_train, X_test, y_test, is_regression=False)
