from typing import List

from walaris.disentanglement_paper.data.datasets import get_dataset_for_name
from walaris.disentanglement_paper.data.eeg import N_EEG_SUBJECTS
from walaris.disentanglement_paper.datatypes import UqModel, ExperimentConfig
from walaris.disentanglement_paper.models.architectures import get_architecture
from walaris.disentanglement_paper.settings import TEST_MODE, N_REPETITIONS


def get_test_mode_configs() -> List[ExperimentConfig]:
    return [
        get_configs_for_dataset_name("CIFAR10", run_decreasing_dataset_experiments=False,
                                     run_label_noise_experiments=False,
                                     run_ood_class_experiments=True, epochs=1),
        get_configs_for_dataset_name("blobs", run_ood_class_experiments=False, epochs=1,
                                     run_label_noise_experiments=True),
        get_configs_for_dataset_name("Motor Imagery BCI", run_ood_class_experiments=False,
                                     run_decreasing_dataset_experiments=False,
                                     run_label_noise_experiments=True, epochs=1),
        get_configs_for_dataset_name("Fashion MNIST", epochs=1, run_ood_class_experiments=False,
                                     run_decreasing_dataset_experiments=True, run_label_noise_experiments=False),
        get_configs_for_dataset_name("UTKFace", epochs=1, run_ood_class_experiments=False,
                                     run_label_noise_experiments=False,
                                     run_decreasing_dataset_experiments=True)
    ]


def get_configs_for_dataset_name(dataset_name, run_index=1, epochs=100, plotting_mode=False,
                                 run_ood_class_experiments=True,
                                 run_decreasing_dataset_experiments=True,
                                 run_label_noise_experiments=True) -> ExperimentConfig:
    meta_experiments = []
    if run_ood_class_experiments:
        meta_experiments.append("ood_class")
    if run_decreasing_dataset_experiments:
        meta_experiments.append("decreasing_dataset")
    if run_label_noise_experiments:
        meta_experiments.append("label_noise")

    BNN_name_epochs = {"MC-Dropout": epochs,
                       "MC-DropConnect": epochs,
                       "Flipout": epochs * 5,
                       "Deep Ensemble": epochs
    }

    if plotting_mode:  # Special case for plotting multiple results. The run-index will be ignored
        dataset_name_for_config = dataset_name
        dataset = None
        is_regression = False

    else:
        dataset_name_for_config = f"{dataset_name} {run_index}"
        dataset = get_dataset_for_name(dataset_name, run_index)
        is_regression = dataset.is_regression

    return ExperimentConfig(
            dataset_name=dataset_name_for_config,
            dataset=dataset,
            models=[UqModel(get_architecture(dataset_name, bnn_name=bnn_name, is_regression=is_regression), bnn_name, epochs=epochs)
                    for bnn_name, epochs in BNN_name_epochs.items()],
            meta_experiments=meta_experiments,
        )


def get_configs_for_dataset_name_repetitions_and_plotting(n_repetitions=N_REPETITIONS, **kwargs) \
        -> List[ExperimentConfig]:
    return [*[get_configs_for_dataset_name(**kwargs, run_index=i) for i in range(n_repetitions)],
            get_configs_for_dataset_name(**kwargs, plotting_mode=True)]


def get_experiment_configs() -> List[ExperimentConfig]:
    if TEST_MODE:
        return get_test_mode_configs()

    return [
        *get_configs_for_dataset_name_repetitions_and_plotting(dataset_name="CIFAR10"),
        *get_configs_for_dataset_name_repetitions_and_plotting(dataset_name="blobs", run_ood_class_experiments=False),
        *get_configs_for_dataset_name_repetitions_and_plotting(dataset_name="Motor Imagery BCI",
                                                               n_repetitions=N_EEG_SUBJECTS),
        *get_configs_for_dataset_name_repetitions_and_plotting(dataset_name="Fashion MNIST"),
        *get_configs_for_dataset_name_repetitions_and_plotting(dataset_name="Wine"),
        *get_configs_for_dataset_name_repetitions_and_plotting(dataset_name="AutoMPG", run_ood_class_experiments=False),
        *get_configs_for_dataset_name_repetitions_and_plotting(dataset_name="UTKFace", run_ood_class_experiments=False),
    ]


