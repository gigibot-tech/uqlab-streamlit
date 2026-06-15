import numpy as np
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D

from walaris.disentanglement_paper.datatypes import UncertaintyResults


def plot_ale_epi_acc_on_axes(ax, results: UncertaintyResults, accuracy_y_ax_to_share=None, is_final_column=False,
                             std=None):
    if not results:
        return

    plot_line_and_confidence_interval(ax, results, std, 'epistemic_uncertainties', label="Epi")
    plot_line_and_confidence_interval(ax, results, std, 'aleatoric_uncertainties', label="Ale")

    accuracy_axes = ax.twinx()

    plot_line_and_confidence_interval(accuracy_axes, results, std, 'accuracies', label="Accuracy", color='green')

    if accuracy_y_ax_to_share:
        accuracy_axes.sharey(accuracy_y_ax_to_share)

    if is_final_column:
        accuracy_axes.set_ylabel("Accuracy", color='green')
    else:
        plt.setp(accuracy_axes.get_yticklabels(), visible=False)

    return accuracy_axes


def plot_line_and_confidence_interval(ax, results, std, get_string, label, color=None):
    plot_lines = ax.plot(results.changed_parameter_values, results.__getattribute__(get_string), label=label, color=color)
    color = plot_lines[0].get_color()
    if std:
        plot_confidence_intervals(ax, results, std, get_string, label=f"_{label}", color=color)


def plot_confidence_intervals(ax, results, std, get_string, label, color=None):
    uncertainties_mean = np.array(results.__getattribute__(get_string))
    uncertainties_std = np.array(std.__getattribute__(get_string))
    ax.fill_between(results.changed_parameter_values,
                    uncertainties_mean - 1.96 * uncertainties_std,
                    uncertainties_mean + 1.96 * uncertainties_std,
                    alpha=0.3, label=label, color=color)


def plot_results_on_idx(results, results_std, arch_idx, axes, experiment_config, architecture, meta_experiment_name, accuracy_y_ax_to_share):
    ## PLOTTING
    is_first_column = arch_idx == 0
    is_final_column = arch_idx == len(experiment_config.models) - 1

    for disentanglement_idx, (disentanglement_name, disentanglement_results) in enumerate(results.items()):
        if results_std:
            disentanglement_results_std = results_std[disentanglement_name]
        else:
            disentanglement_results_std = None

        if np.isnan(disentanglement_results.accuracies[0]):
            continue  # There's no results to plot!
        accuracy_y_ax_to_share = plot_ale_epi_acc_on_axes(axes[disentanglement_idx][arch_idx],
                                                          disentanglement_results,
                                                          accuracy_y_ax_to_share, is_final_column,
                                                          std=disentanglement_results_std)
        ## ADD HEADERS & LEGEND TO FIRST COLUMN
        if is_first_column:

            disentanglement_plot_name = {
                "it": "Information Theoretic",
                "gaussian_logits": "Gaussian Logits"
            }[disentanglement_name]

            axes[disentanglement_idx][arch_idx].set_ylabel(f"{disentanglement_plot_name}\nUncertainty")

    axes[0][arch_idx].set_title(architecture.uq_name)

    meta_experiment_xlabel = {
        "decreasing_dataset": "Dataset size",
        "label_noise": "Labels shuffled"
    }[meta_experiment_name]
    axes[-1][arch_idx].set_xlabel(meta_experiment_xlabel)

    if is_first_column:
        handles, labels = axes[0][arch_idx].get_legend_handles_labels()

        labels.append("Acc")
        line = Line2D([0], [0], label='Acc', color='green')
        handles.append(line)

        axes[0][arch_idx].legend(handles=handles, labels=labels, loc='upper left', fontsize=10)

    return accuracy_y_ax_to_share
