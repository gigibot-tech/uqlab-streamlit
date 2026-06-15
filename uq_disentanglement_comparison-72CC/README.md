# Uncertainty Disentanglement
Uncertainty Quantification methods for Neural Networks can make separate predictions for aleatoric and epistemic uncertainty.
This repository implements three experiments that manipulate the underlying aleatoric or epistemic uncertainty, and observes adverse interactions.

The experiments are conducted with different datasets, UQ methods, and disentanglement methods.

# Installation

Create a virtual environment and install dependencies with Pipenv
```bash
python3 -m venv ./venv
source ./venv/bin/activation
pip install pipenv
pipenv install
```

# Usage
You can run the experiments with the simple command `python3 main.py`.
Out of the box, this will run all experiments and take several days to complete.
We recommend first modifying the `disentanglement.experiment_configs.get_experiment_configs()` to select the conditions you are interested in.

Additionally `disentanglement/settings.py` has various hyperparameters that can be used to modify the experiment setup. 
It includes a `TEST_MODE` which runs through all experiments but changes hyperparameters to minimize compute cost. 
The results become meaningless, but will show whether things work.


# Navigating the project
The project comes with three main components:
- The experiments and plotting in `disentanglement/benchmarks`
- The data loading and preprocessing in `disentanglement/data`
- The UQ methods, architectures and disentangling methods in `disentanglement/models`

These all come together in the `experiments_configs.py` which gives the set of benchmarks, models, and datasets to run together.
By default, all results are stored to file through `util.py`. If the results already exist, the experiment will skip over those experiments.

Additionally, the `notebooks` folder has some jupyter notebooks which contain smaller experiments and additional investigations. 

# Attribution and context

This repository run the experiments from [**"Measuring Uncertainty Disentanglement Error in Classification"** 
by Ivo Pascal de Jong, Andreea Ioana Sburlea, Matthia Sabatelli & Matias Valdenegro-Toro](https://arxiv.org/abs/2408.12175).
We additionally provide a [separate repository for calcutaing Disentanglement Error](XXXX-1).

For attribution please cite:

```text
@article{de2024disentangled,
  title={Measuring Uncertainty Disentanglement Error in Classification},
  author={de Jong, Ivo Pascal and Sburlea, Andreea Ioana, Sabatelli, Matthia and Valdenegro-Toro, Matias},
  journal={arXiv preprint arXiv:2408.12175},
  year={2024}
}
```
