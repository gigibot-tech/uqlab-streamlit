"""Keras paper benchmark entry point (requires tensorflow + keras)."""

from __future__ import annotations

import gc
import os.path
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")


def main() -> None:
    import keras.backend as K
    import matplotlib.pyplot as plt
    import seaborn as sns
    import tensorflow as tf

    from walaris.disentanglement_paper.benchmarks.decreasing_dataset import (
        plot_decreasing_dataset,
    )
    from walaris.disentanglement_paper.benchmarks.label_noise import label_noise
    from walaris.disentanglement_paper.benchmarks.ood_class_detection import (
        plot_ood_class_detection,
    )
    from walaris.disentanglement_paper.experiment_configs import get_experiment_configs
    from walaris.disentanglement_paper.settings import GPU_INDEX, TEST_MODE

    os.environ["CUDA_VISIBLE_DEVICES"] = GPU_INDEX
    physical_devices = tf.config.list_physical_devices("GPU")
    plt.rcParams["axes.grid"] = False
    sns.reset_orig()

    if physical_devices:
        tf.config.experimental.set_memory_growth(physical_devices[0], True)

    tf.get_logger().setLevel("ERROR")

    start_time = datetime.now()
    experiment_configs = get_experiment_configs()
    from_folder = True

    if TEST_MODE:
        from_folder = False

    if not os.path.exists("./figures"):
        os.mkdir("./figures")
    for experiment_config in experiment_configs:
        has_dataset = experiment_config.dataset is None

        if "decreasing_dataset" in experiment_config.meta_experiments:
            plot_decreasing_dataset(
                experiment_config, from_folder=(has_dataset or from_folder)
            )
        if "label_noise" in experiment_config.meta_experiments:
            label_noise(experiment_config, from_folder=(has_dataset or from_folder))
        if "ood_class" in experiment_config.meta_experiments:
            plot_ood_class_detection(
                experiment_config, from_folder=(has_dataset or from_folder)
            )
        experiment_config.dataset = None
        K.clear_session()
        gc.collect()

    end_time = datetime.now()
    print(f"Ran all experiments in {end_time - start_time}")


if __name__ == "__main__":
    main()
