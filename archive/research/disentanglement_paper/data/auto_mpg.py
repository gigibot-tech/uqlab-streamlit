from functools import lru_cache

import numpy as np
from sklearn.preprocessing import StandardScaler

from uqlab.disentanglement_paper.datatypes import Dataset
import pandas as pd


@lru_cache(maxsize=None)
def get_train_test_auto_mpg_regression() -> Dataset:
    url = 'http://archive.ics.uci.edu/ml/machine-learning-databases/auto-mpg/auto-mpg.data'
    column_names = ['MPG', 'Cylinders', 'Displacement', 'Horsepower', 'Weight',
                    'Acceleration', 'Model Year', 'Origin']

    raw_dataset = pd.read_csv(url, names=column_names,
                              na_values='?', comment='\t',
                              sep=' ', skipinitialspace=True)
    dataset = raw_dataset.copy()
    dataset = dataset.dropna()

    dataset['Origin'] = dataset['Origin'].map({1: 'USA', 2: 'Europe', 3: 'Japan'})
    dataset = pd.get_dummies(dataset, columns=['Origin'], prefix='', prefix_sep='')
    train_dataset = dataset.sample(frac=0.8, random_state=0)
    test_dataset = dataset.drop(train_dataset.index)

    train_features = train_dataset.copy()
    test_features = test_dataset.copy()

    train_labels = train_features.pop('MPG')
    test_labels = test_features.pop('MPG')

    normalizer = StandardScaler()
    normalizer.fit(train_features)
    train_features = normalizer.transform(train_features)
    test_features = normalizer.transform(test_features)

    return Dataset(np.array(train_features).astype('float32'), np.array(train_labels).astype('float32'),
                   np.array(test_features).astype('float32'), np.array(test_labels).astype('float32'),
                   is_regression=True)
