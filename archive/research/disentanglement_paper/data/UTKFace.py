import os

import numpy as np
import pandas as pd
from functools import lru_cache
from PIL import Image
from uqlab.disentanglement_paper.datatypes import Dataset
from sklearn.model_selection import train_test_split
from tqdm import tqdm
from sklearn.utils import shuffle
from keras.preprocessing.image import load_img


def fetch_images(images):
    features = []
    for image in tqdm(images):
        img = load_img(image)
        img = img.resize((128, 128), Image.LANCZOS)
        img = np.array(img)
        features.append(img)
    features = np.array(features)
    return features


@lru_cache(maxsize=None)
def get_train_test_utkface_regression():
    base_dir = 'datasets/UTKFace/'

    image_paths = []
    age_labels = []
    gender_labels = []

    for filename in tqdm(os.listdir(base_dir)):
        image_path = os.path.join(base_dir, filename)
        temp = filename.split('_')
        age = int(temp[0])
        gender = int(temp[1])
        image_paths.append(image_path)
        age_labels.append(age)
        gender_labels.append(gender)

    df = pd.DataFrame()
    df['image'], df['age'], df['gender'] = image_paths, age_labels, gender_labels
    df = shuffle(df)

    df = df[df['age'] <= 60]  # Constrain to 21-60 according to "Deep Ordinal Regression with Label Diversity"
    df = df[df['age'] > 20]

    X = fetch_images(df['image'])
    X = X / 255.0
    y_age = np.array(df['age'])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_age, test_size=0.2, random_state=0)

    return Dataset(X_train, y_train, X_test, y_test, is_regression=True)

