import numpy as np
from moabb.datasets import BNCI2014_001
from moabb.paradigms import MotorImagery
from sklearn.preprocessing import LabelEncoder
from functools import lru_cache
from walaris.disentanglement_paper.datatypes import Dataset

N_EEG_SUBJECTS = 9


@lru_cache(maxsize=None)
def get_eeg_data(subject_id):
    dataset = BNCI2014_001()        # load dataset
    paradigm = MotorImagery(        # make paradigm, filter between 7.5 and 30 Hz
        n_classes=4, fmin=7.5, fmax=30, tmin=0, tmax=None, resample=128
    )

    X, y, metadata = paradigm.get_data(dataset=dataset, subjects=[subject_id + 1])
    X = np.expand_dims(X, -1)

    le = LabelEncoder()
    y = le.fit_transform(y)
    return Dataset(X[metadata.session == "0train"], y[metadata.session == "0train"],
                   X[metadata.session == "1test"], y[metadata.session == "1test"], is_regression=False)
