from keras import Sequential, Input
from keras.src.constraints import max_norm
from keras.src.layers import Dense, Conv2D, MaxPooling2D, Flatten, BatchNormalization, Activation, AveragePooling2D
from keras import backend as K


def get_wine_backbone(input_shape=13):
    model = Sequential()
    model.add(Input(input_shape))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(32, activation='relu'))

    return model


def get_auto_mpg_backbone(input_shape=9):
    model = Sequential()
    model.add(Input(input_shape))
    model.add(Dense(16, activation='relu'))

    return model


def get_utkface_convolutional_blocks(input_shape=(128, 128, 3)):
    model = Sequential()
    model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=input_shape))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
    model.add(Conv2D(256, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Flatten())

    return model


def get_cifar10_convolutional_blocks(input_shape=(32, 32, 3)):
    model = Sequential()
    model.add(Conv2D(32, (3, 3), activation='relu', input_shape=input_shape))
    model.add(MaxPooling2D((2, 2)))
    model.add(Conv2D(64, (3, 3), activation='relu'))
    model.add(MaxPooling2D((2, 2)))
    model.add(Conv2D(64, (3, 3), activation='relu'))
    model.add(Flatten())

    return model


def get_fashion_mnist_convolutional_blocks():
    return get_cifar10_convolutional_blocks(input_shape=(28, 28, 1))


# need these for ShallowConvNet
def square(x):
    return K.square(x)


def log(x):
    return K.log(K.clip(x, min_value=1e-7, max_value=10000))


def get_eeg_convolutional_blocks(channels=22, samples=513):
    # This is based off ShallowConvNet, but we can add a (Bayesian) FC layer after the conv block
    model = Sequential()
    model.add(Conv2D(40, (1, 13),
                     input_shape=(channels, samples, 1),
                     kernel_constraint=max_norm(2., axis=(0, 1, 2))))
    model.add(Conv2D(40, (channels, 1), use_bias=False,
                     kernel_constraint=max_norm(2., axis=(0, 1, 2))))
    model.add(BatchNormalization(epsilon=1e-05, momentum=0.9))
    model.add(Activation(square))
    model.add(AveragePooling2D(pool_size=(1, 35), strides=(1, 7)))
    model.add(Activation(log))
    model.add(Flatten())

    return model


def get_blobs_backbone(input_shape=(2,)):
    model = Sequential()
    model.add(Dense(32, activation='relu', input_shape=input_shape))
    return model
