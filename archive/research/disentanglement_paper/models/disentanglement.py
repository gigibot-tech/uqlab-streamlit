from uqlab.disentanglement_paper.models.information_theoretic_models import get_average_uncertainty_it

from uqlab.disentanglement_paper.models.gaussian_logits_models import get_average_uncertainty_gaussian_logits
from uqlab.disentanglement_paper.models.logit_variance import get_average_uncertainty_logit_variance

DISENTANGLEMENT_FUNCS = {
    "gaussian_logits": get_average_uncertainty_gaussian_logits,
    "it": get_average_uncertainty_it,
    # "logit_variance": get_average_uncertainty_logit_variance,
}