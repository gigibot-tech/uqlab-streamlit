from walaris.disentanglement_paper.data.UTKFace import get_train_test_utkface_regression
from walaris.disentanglement_paper.data.auto_mpg import get_train_test_auto_mpg_regression
from walaris.disentanglement_paper.data.eeg import get_eeg_data

from walaris.disentanglement_paper.data.blobs import get_train_test_blobs

from walaris.disentanglement_paper.data.cifar10 import get_train_test_cifar_10
from walaris.disentanglement_paper.data.fashion_mnist import get_train_test_fashion_mnist
from walaris.disentanglement_paper.data.wine import get_train_test_wine


def get_dataset_for_name(dataset_name, run_index):
    match dataset_name:
        case "CIFAR10":
            return get_train_test_cifar_10()
        case "Motor Imagery BCI":
            return get_eeg_data(run_index)
        case "blobs":
            return get_train_test_blobs()
        case "Fashion MNIST":
            return get_train_test_fashion_mnist()
        case "Wine":
            return get_train_test_wine()
        case "AutoMPG":
            return get_train_test_auto_mpg_regression()
        case "UTKFace":
            return get_train_test_utkface_regression()

    raise ValueError(f"No dataset implemented for {dataset_name}")
