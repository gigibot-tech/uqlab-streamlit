"""
Single entrypoint for the data pipeline — config to train/eval tensor packs.

Call :func:`build_run_data` once.

Internal sequence:
  1. ``step1_load_dataset_and_splits`` — registry load + index splits
  2. ``step2_materialize_tensor_packs`` — SplitSpec → torch packs (embeddings or images)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional

import numpy as np
import torch
from torch.utils.data import Dataset
from torchvision import transforms

from uqlab_core.data.datasets.registry import (
    dataset_clean_labels,
    get_dataset_spec,
    load_classification_dataset,
)
from uqlab_core.data.splits.experiment_loader import (
    SplitSpec,
    expects_aleatoric_eval,
    expects_epistemic_eval,
    sample_indices_for_experiment,
)
from uqlab_core.data.splits.four_region import normalize_class_regions
from uqlab_core.models.factory.classification_models import EmbeddingDataset
from uqlab_core.models.features.feature_extractors import DINOv2FeatureExtractor, create_feature_extractor
from uqlab_core.models.scope.architecture import normalize_architecture
from uqlab_core.run_artifacts import GROUP_ALEATORIC, GROUP_CLEAN, GROUP_EPISTEMIC, GROUP_OOD
from uqlab_core.shared.config.classification import ExperimentConfig, TrainingConfig
from uqlab_core.shared.utils.classification import dino_transform

logger = logging.getLogger(__name__)

RunDataMode = Literal["embeddings", "images"]

EVAL_PACK_KEYS = frozenset(
    {"features", "noisy_labels", "clean_labels", "is_noisy", "original_indices"}
)

# --- Step 1: load dataset + build SplitSpec ---

@dataclass(frozen=True)
class PilotDataRequest:
    """Normalized data-phase inputs extracted from ``ExperimentConfig``."""

    dataset_name: str
    num_classes: int
    data_root: Path
    noise_type: str
    effective_noise_type: str
    aleatoric_noise_percentage: Optional[float]
    alea_for_load: Optional[float]
    under_supported_classes: list[int]
    under_train_per_class: int
    regular_train_per_class: int
    eval_per_group: int
    partition_mode: str = "legacy"
    class_regions: Optional[dict] = None
    per_class_config: Optional[dict] = None


@dataclass
class ExperimentDataContext:
    """Outputs of the data phase shared by facade coordinators and the runner."""

    dataset: object
    split_spec: SplitSpec
    dataset_name: str
    num_classes: int
    data_root: Path
    noise_type: str
    effective_noise_type: str
    aleatoric_noise_percentage: Optional[float]
    alea_for_load: Optional[float]
    under_supported_classes: list[int]
    request: PilotDataRequest | None = None

    @classmethod
    def from_request(
        cls,
        request: PilotDataRequest,
        *,
        dataset: object,
        split_spec: SplitSpec,
    ) -> ExperimentDataContext:
        return cls(
            dataset=dataset,
            split_spec=split_spec,
            dataset_name=request.dataset_name,
            num_classes=request.num_classes,
            data_root=request.data_root,
            noise_type=request.noise_type,
            effective_noise_type=request.effective_noise_type,
            aleatoric_noise_percentage=request.aleatoric_noise_percentage,
            alea_for_load=request.alea_for_load,
            under_supported_classes=list(request.under_supported_classes),
            request=request,
        )


def _resolve_data_root(config: ExperimentConfig, project_root: Path) -> Path:
    root = Path(getattr(config.paths, "data_root", None) or config.paths.cifar10n_root)
    return root if root.is_absolute() else project_root / root


def _noise_pct_for_dataset_load(
    *,
    dataset_name: str,
    noise_type: str,
    aleatoric_noise_percentage: Optional[float],
) -> Optional[float]:
    """
    How much synthetic noise to inject when calling ``load_classification_dataset``.

    - Explicit sweep percentage > 0 → inject that much on ``cifar10`` / ``mnist``.
    - ``cifar10n`` with a human-noise split → ``None`` (loader uses ``noise_type``).
    - Otherwise → ``0.0`` (clean labels).
    """
    if aleatoric_noise_percentage is not None and aleatoric_noise_percentage > 0:
        return float(aleatoric_noise_percentage)
    if dataset_name == "cifar10n" and noise_type not in (
        "clean_label",
        "none",
        "clean",
        "no_noise",
    ):
        return None
    return 0.0


def parse_pilot_data_request(
    config: ExperimentConfig,
    project_root: Path,
) -> PilotDataRequest:
    """Read and normalize ``config.data`` + ``config.paths`` for the data phase."""
    if config.data is None or config.paths is None:
        raise ValueError("ExperimentConfig.data and .paths are required")

    data = config.data
    dataset_name = getattr(data, "dataset_name", None) or "cifar10"
    ds_spec = get_dataset_spec(dataset_name)
    noise_type = data.noise_type
    aleatoric_noise_percentage = data.aleatoric_noise_percentage
    under_supported_classes = list(data.under_supported_classes or [])
    partition_mode = str(getattr(data, "partition_mode", "legacy") or "legacy")
    class_regions = getattr(data, "class_regions", None)
    per_class_config = getattr(data, "per_class_config", None)
    if per_class_config is not None:
        partition_mode = "per_class"
    if partition_mode == "four_region":
        class_regions = normalize_class_regions(class_regions)
        sparse = class_regions.get("sparse", {}).get("classes") or []
        if sparse:
            under_supported_classes = [int(c) for c in sparse]

    effective_noise_type = noise_type
    if partition_mode == "four_region":
        effective_noise_type = "clean_label"
        aleatoric_noise_percentage = 0.0
    elif aleatoric_noise_percentage == 0:
        effective_noise_type = "clean_label"

    alea_for_load = _noise_pct_for_dataset_load(
        dataset_name=dataset_name,
        noise_type=noise_type,
        aleatoric_noise_percentage=aleatoric_noise_percentage,
    )
    if partition_mode == "four_region":
        alea_for_load = 0.0

    return PilotDataRequest(
        dataset_name=dataset_name,
        num_classes=ds_spec.num_classes,
        data_root=_resolve_data_root(config, project_root),
        noise_type=noise_type,
        effective_noise_type=effective_noise_type,
        aleatoric_noise_percentage=aleatoric_noise_percentage,
        alea_for_load=alea_for_load,
        under_supported_classes=under_supported_classes,
        under_train_per_class=int(data.under_train_per_class),
        regular_train_per_class=int(data.regular_train_per_class)
        if data.regular_train_per_class is not None
        else int(data.under_train_per_class),
        eval_per_group=int(data.eval_per_group),
        partition_mode=partition_mode,
        class_regions=class_regions,
        per_class_config=per_class_config,
    )


def validate_pilot_data_request(request: PilotDataRequest) -> None:
    """Fail fast on invalid budgets before touching disk."""
    if request.regular_train_per_class < 0:
        raise ValueError(f"Invalid regular_train_per_class={request.regular_train_per_class}")
    if request.under_train_per_class < 0:
        raise ValueError(f"Invalid under_train_per_class={request.under_train_per_class}")
    if request.eval_per_group <= 0:
        raise ValueError(f"Invalid eval_per_group={request.eval_per_group}")

    if request.partition_mode == "per_class":
        raise NotImplementedError(
            "partition_mode=per_class is configured but not yet implemented in the "
            "data pipeline; use legacy or four_region"
        )

    if request.partition_mode == "four_region":
        if not request.class_regions:
            raise ValueError("class_regions required when partition_mode=four_region")
        from uqlab_core.data.splits.four_region import validate_class_regions

        validate_class_regions(request.class_regions, num_classes=request.num_classes)
        return

    if not request.under_supported_classes:
        raise ValueError("under_supported_classes must specify at least one class")

    for cls in request.under_supported_classes:
        if cls < 0 or cls >= request.num_classes:
            raise ValueError(
                f"Invalid class {cls} in under_supported_classes "
                f"(valid: 0..{request.num_classes - 1})"
            )


def load_pilot_dataset(request: PilotDataRequest, *, seed: int = 42) -> object:
    """Download/load the full training split via the dataset registry."""
    logger.info(
        "Loading %s via dataset factory (root=%s, alea_for_load=%s)",
        request.dataset_name,
        request.data_root,
        request.alea_for_load,
    )
    dataset = load_classification_dataset(
        request.dataset_name,
        root=request.data_root,
        noise_type=request.noise_type,
        aleatoric_noise_percentage=request.alea_for_load,
        train=True,
        download=True,
        transform=dino_transform(),
    )
    if getattr(dataset, "noise_mask", None) is not None:
        logger.info(
            "Loaded %s samples, noise rate %.2f%%",
            len(dataset),
            float(getattr(dataset, "noise_rate", 0)) * 100,
        )
    else:
        logger.info("Loaded %s samples", len(dataset))
    return dataset


def build_pilot_split_spec(request: PilotDataRequest, dataset: object, *, seed: int) -> SplitSpec:
    """Sample train/eval index pools (clean / aleatoric-like / epistemic-like / optional OOD)."""
    if request.partition_mode == "per_class":
        raise NotImplementedError(
            "partition_mode=per_class is configured but not yet implemented in the "
            "data pipeline; use legacy or four_region"
        )

    if request.partition_mode == "four_region":
        from uqlab_core.data.splits.four_region import build_split_spec

        return build_split_spec(request, dataset, seed=seed)

    split_spec = sample_indices_for_experiment(
        dataset,
        under_supported_classes=request.under_supported_classes,
        under_train_per_class=request.under_train_per_class,
        regular_train_per_class=request.regular_train_per_class,
        eval_per_group=request.eval_per_group,
        seed=seed,
        aleatoric_noise_percentage=request.aleatoric_noise_percentage or 0.0,
    )
    logger.info(
        "Splits: train=%s clean=%s aleatoric=%s epistemic=%s ood=%s",
        len(split_spec.train_indices),
        len(split_spec.clean_eval_indices),
        len(split_spec.aleatoric_eval_indices),
        len(split_spec.epistemic_eval_indices),
        len(split_spec.ood_eval_indices),
    )
    return split_spec


def validate_pilot_split_spec(request: PilotDataRequest, split_spec: SplitSpec) -> None:
    """Ensure expected benchmark pools exist for the configured axes."""
    all_empty = (
        len(split_spec.clean_eval_indices) == 0
        and len(split_spec.aleatoric_eval_indices) == 0
        and len(split_spec.epistemic_eval_indices) == 0
        and len(split_spec.ood_eval_indices) == 0
    )
    if all_empty:
        raise RuntimeError("All evaluation groups are empty — check training/eval budget.")

    if len(split_spec.aleatoric_eval_indices) == 0 and expects_aleatoric_eval(
        request.aleatoric_noise_percentage
    ):
        raise RuntimeError(
            f"Aleatoric benchmark requested ({request.aleatoric_noise_percentage}% noise) "
            "but aleatoric eval pool is empty."
        )

    if len(split_spec.epistemic_eval_indices) == 0 and expects_epistemic_eval(
        request.under_supported_classes,
        under_train_per_class=request.under_train_per_class,
        regular_train_per_class=request.regular_train_per_class,
    ):
        logger.warning("Epistemic eval pool is empty — epistemic AUROC will be NaN.")


def step1_load_dataset_and_splits(
    config: ExperimentConfig,
    project_root: Path,
    *,
    seed: int,
) -> ExperimentDataContext:
    """Step 1: load dataset from registry and sample train/eval index splits."""
    request = parse_pilot_data_request(config, project_root)
    validate_pilot_data_request(request)
    dataset = load_pilot_dataset(request, seed=seed)
    split_spec = build_pilot_split_spec(request, dataset, seed=seed)
    validate_pilot_split_spec(request, split_spec)
    return ExperimentDataContext.from_request(request, dataset=dataset, split_spec=split_spec)


def prepare_experiment_data(
    config: ExperimentConfig,
    project_root: Path,
    *,
    seed: int,
) -> ExperimentDataContext:
    """
    Advanced API — prefer :func:`uqlab_core.data.build_run_data`.

    Step 1 only: YAML ``ExperimentConfig`` → loaded dataset + ``SplitSpec``.
    """
    return step1_load_dataset_and_splits(config, project_root, seed=seed)


# --- Step 2: materialize torch packs ---

@dataclass(frozen=True)
class RunDataPacks:
    """Train subset + four eval pools + concatenated eval tensors."""

    train_dataset: Any
    clean_eval_pack: dict[str, torch.Tensor]
    aleatoric_eval_pack: dict[str, torch.Tensor]
    epistemic_eval_pack: dict[str, torch.Tensor]
    ood_eval_pack: dict[str, torch.Tensor]
    eval_data: dict[str, torch.Tensor]
    eval_inputs: torch.Tensor
    mode: RunDataMode
    feature_dim: int | None


def get_data_loading_mode(config: ExperimentConfig) -> RunDataMode:
    """Map ``ModelConfig.training_mode`` to ``embeddings`` or ``images``."""
    model_config = config.model
    if model_config is None:
        raise ValueError("ExperimentConfig.model must be set")

    if model_config.training_mode == "feature_space":
        return "embeddings"
    if model_config.training_mode == "end_to_end":
        return "images"
    raise ValueError(f"Unknown training mode: {model_config.training_mode}")


def resolve_run_data_mode(config: ExperimentConfig) -> RunDataMode:
    """
    Effective run mode after architecture-specific overrides.

    ResNet in ``feature_space`` config uses frozen backbone on images (no DINO cache).
    """
    mode = get_data_loading_mode(config)
    if normalize_architecture(config.model.architecture) == "resnet18" and mode == "embeddings":
        logger.info(
            "ResNet with feature_space mode: Using images with frozen backbone "
            "(ResNet doesn't support feature caching like DINOv2)"
        )
        return "images"
    return mode


def prepare_eval_tensors(
    clean_eval_pack: dict,
    aleatoric_eval_pack: dict,
    epistemic_eval_pack: dict,
    ood_eval_pack: dict | None = None,
) -> dict[str, torch.Tensor]:
    """Concatenate eval packs into shared tensors (group labels, indices, inputs)."""
    packs: list[tuple[dict, int]] = [
        (clean_eval_pack, GROUP_CLEAN),
        (aleatoric_eval_pack, GROUP_ALEATORIC),
        (epistemic_eval_pack, GROUP_EPISTEMIC),
    ]
    if ood_eval_pack is not None and len(ood_eval_pack.get("features", [])) > 0:
        packs.append((ood_eval_pack, GROUP_OOD))

    eval_inputs = torch.cat([p["features"] for p, _ in packs], dim=0)
    eval_group_labels = torch.cat(
        [torch.full((len(p["features"]),), code, dtype=torch.long) for p, code in packs],
        dim=0,
    )
    eval_clean_labels = torch.cat([p["clean_labels"] for p, _ in packs], dim=0)
    eval_is_noisy = torch.cat([p["is_noisy"] for p, _ in packs], dim=0)
    eval_noisy_labels = torch.cat([p["noisy_labels"] for p, _ in packs], dim=0)
    eval_dataset_index = torch.cat([p["original_indices"] for p, _ in packs], dim=0)
    return {
        "eval_inputs": eval_inputs,
        "eval_group_labels": eval_group_labels,
        "eval_clean_labels": eval_clean_labels,
        "eval_is_noisy": eval_is_noisy,
        "eval_noisy_labels": eval_noisy_labels,
        "eval_dataset_index": eval_dataset_index,
    }


prepare_eval_data = prepare_eval_tensors


def _packs_from_embedding_extractor(
    feature_extractor: DINOv2FeatureExtractor,
) -> tuple[Any, dict, dict, dict, dict, int]:
    feature_extractor.organizer.load_or_compute_features()

    train_pack = feature_extractor.get_train_pack()
    clean_eval_pack = feature_extractor.get_clean_eval_pack()
    aleatoric_eval_pack = feature_extractor.get_aleatoric_eval_pack()
    epistemic_eval_pack = feature_extractor.get_epistemic_eval_pack()
    ood_eval_pack = feature_extractor.get_ood_eval_pack()

    train_dataset = EmbeddingDataset(
        train_pack["features"],
        train_pack["noisy_labels"],
        train_pack["clean_labels"],
        train_pack["is_noisy"],
        train_pack["original_indices"],
    )
    feature_dim = int(train_pack["features"].shape[1])
    return (
        train_dataset,
        clean_eval_pack,
        aleatoric_eval_pack,
        epistemic_eval_pack,
        ood_eval_pack,
        feature_dim,
    )


# --- Image-mode transforms + subset datasets ---

CIFAR10_MEAN = (0.4914, 0.4822, 0.4465)
CIFAR10_STD = (0.2023, 0.1994, 0.2010)
MNIST_MEAN_3CH = (0.1307, 0.1307, 0.1307)
MNIST_STD_3CH = (0.3081, 0.3081, 0.3081)


class _RepeatChannels:
    """Picklable 1→N channel repeat (DataLoader workers require picklable transforms)."""

    def __init__(self, times: int = 3) -> None:
        self.times = times

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        return x.repeat(self.times, 1, 1)


def get_dataset_image_transform(dataset_name: str) -> transforms.Compose:
    """End-to-end image transforms keyed by dataset registry name."""
    name = (dataset_name or "cifar10").lower()
    if name in ("mnist", "fashion_mnist"):
        return transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((32, 32)),
            _RepeatChannels(3),
            transforms.Normalize(MNIST_MEAN_3CH, MNIST_STD_3CH),
        ])
    return transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(CIFAR10_MEAN, CIFAR10_STD),
    ])


class ClassificationImageDataset(Dataset):
    """Subset wrapper returning image tensors with labels/metadata."""

    def __init__(self, base_dataset, indices, transform=None):
        self.base_dataset = base_dataset
        self.indices = np.asarray(indices, dtype=np.int64)
        self.transform = transform

        clean_labels = dataset_clean_labels(base_dataset)
        if base_dataset.noisy_labels is not None and base_dataset.noise_mask is not None:
            noisy_labels = np.asarray(base_dataset.noisy_labels)
            is_noisy = np.asarray(base_dataset.noise_mask, dtype=bool)
        else:
            noisy_labels = clean_labels.copy()
            is_noisy = np.zeros(len(base_dataset), dtype=bool)

        self.targets = torch.as_tensor(noisy_labels[self.indices], dtype=torch.long)
        self.clean_labels = torch.as_tensor(clean_labels[self.indices], dtype=torch.long)
        self.is_noisy = torch.as_tensor(is_noisy[self.indices], dtype=torch.bool)
        self.original_indices = torch.as_tensor(self.indices, dtype=torch.long)

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, item: int):
        dataset_index = int(self.indices[item])
        image = self.base_dataset.get_image(dataset_index)
        if self.transform is not None:
            image = self.transform(image)
        return image, self.targets[item]


CIFAR10NImageDataset = ClassificationImageDataset


def load_image_datasets(
    dataset,
    split_spec: SplitSpec,
    *,
    dataset_name: str = "cifar10",
) -> tuple[ClassificationImageDataset, dict[str, dict[str, torch.Tensor]]]:
    """Build train subset and eval packs for image-mode training."""
    transform = get_dataset_image_transform(dataset_name)
    train_dataset = ClassificationImageDataset(
        dataset, split_spec.train_indices, transform=transform
    )

    def build_eval_pack(indices: np.ndarray) -> dict[str, torch.Tensor]:
        subset = ClassificationImageDataset(dataset, indices, transform=transform)
        images = (
            torch.stack([subset[i][0] for i in range(len(subset))], dim=0)
            if len(subset) > 0
            else torch.empty((0, 3, 32, 32), dtype=torch.float32)
        )
        return {
            "inputs": images,
            "features": images,
            "noisy_labels": subset.targets,
            "clean_labels": subset.clean_labels,
            "is_noisy": subset.is_noisy,
            "original_indices": subset.original_indices,
        }

    eval_packs = {
        "clean": build_eval_pack(split_spec.clean_eval_indices),
        "aleatoric": build_eval_pack(split_spec.aleatoric_eval_indices),
        "epistemic": build_eval_pack(split_spec.epistemic_eval_indices),
        "ood": build_eval_pack(split_spec.ood_eval_indices),
    }
    return train_dataset, eval_packs


def _packs_from_images(
    dataset,
    split_spec: SplitSpec,
    *,
    dataset_name: str,
) -> tuple[Any, dict, dict, dict, dict]:
    train_dataset, eval_packs = load_image_datasets(
        dataset, split_spec, dataset_name=dataset_name
    )
    return (
        train_dataset,
        eval_packs["clean"],
        eval_packs["aleatoric"],
        eval_packs["epistemic"],
        eval_packs["ood"],
    )


def _finalize_run_packs(
    *,
    train_dataset,
    clean_eval_pack: dict,
    aleatoric_eval_pack: dict,
    epistemic_eval_pack: dict,
    ood_eval_pack: dict,
    mode: RunDataMode,
    feature_dim: int | None,
) -> RunDataPacks:
    eval_data = prepare_eval_tensors(
        clean_eval_pack,
        aleatoric_eval_pack,
        epistemic_eval_pack,
        ood_eval_pack,
    )
    return RunDataPacks(
        train_dataset=train_dataset,
        clean_eval_pack=clean_eval_pack,
        aleatoric_eval_pack=aleatoric_eval_pack,
        epistemic_eval_pack=epistemic_eval_pack,
        ood_eval_pack=ood_eval_pack,
        eval_data=eval_data,
        eval_inputs=eval_data["eval_inputs"],
        mode=mode,
        feature_dim=feature_dim,
    )


def prepare_run_data_context(
    *,
    config: ExperimentConfig,
    dataset,
    split_spec: SplitSpec,
    dataset_name: str,
    device: torch.device,
    feature_cache_dir: Path,
    noise_type: str,
    feature_batch_size: int,
    ds_spec=None,
) -> dict[str, Any]:
    """
    Build train/eval packs for one run (embeddings or images).

    Advanced API — prefer :func:`uqlab_core.data.build_run_data`.
    Called after step 1 (dataset + ``SplitSpec``). Does not train the model.
    """
    del ds_spec  # kept for call-site compatibility with experiment_core

    if config.model is not None:
        from uqlab_core.models.backbones.dinov2_backbone import DINOv2Backbone

        normalized = DINOv2Backbone.normalize_model_name(config.model.dinov2_model)
        if normalized != config.model.dinov2_model:
            config.model.dinov2_model = normalized

    mode = resolve_run_data_mode(config)
    feature_dim: int | None = None

    if mode == "embeddings":
        feature_extractor = create_feature_extractor(
            config.model,
            device=device,
            dataset=dataset,
            split_spec=split_spec,
            feature_cache_dir=feature_cache_dir,
            noise_type=noise_type,
            batch_size=feature_batch_size,
        )
        if not isinstance(feature_extractor, DINOv2FeatureExtractor):
            raise TypeError("Expected DINOv2FeatureExtractor for feature_space mode")

        train_dataset, clean, alea, epis, ood, feature_dim = _packs_from_embedding_extractor(
            feature_extractor
        )
    elif mode == "images":
        train_dataset, clean, alea, epis, ood = _packs_from_images(
            dataset, split_spec, dataset_name=dataset_name
        )
    else:
        raise ValueError(f"Unsupported data loading mode: {mode}")

    packs = _finalize_run_packs(
        train_dataset=train_dataset,
        clean_eval_pack=clean,
        aleatoric_eval_pack=alea,
        epistemic_eval_pack=epis,
        ood_eval_pack=ood,
        mode=mode,
        feature_dim=feature_dim,
    )
    return {
        "train_dataset": packs.train_dataset,
        "clean_eval_pack": packs.clean_eval_pack,
        "aleatoric_eval_pack": packs.aleatoric_eval_pack,
        "epistemic_eval_pack": packs.epistemic_eval_pack,
        "ood_eval_pack": packs.ood_eval_pack,
        "eval_data": packs.eval_data,
        "eval_inputs": packs.eval_inputs,
        "mode": packs.mode,
        "feature_dim": packs.feature_dim,
    }

# --- Public entry ---

@dataclass
class RunDataBundle:
    """Output of :func:`build_run_data` — ready for :func:`run_paper_experiment`."""

    dataset: object
    split_spec: SplitSpec
    data_pack: dict[str, Any]
    request: PilotDataRequest
    ctx: ExperimentDataContext

    @property
    def train_dataset(self) -> Any:
        return self.data_pack["train_dataset"]

    @property
    def mode(self) -> str:
        return self.data_pack["mode"]

    @property
    def feature_dim(self) -> int | None:
        return self.data_pack.get("feature_dim")


def _assert_dinov2_if_needed(config: ExperimentConfig, device: torch.device) -> None:
    if config.model is None:
        return
    mode = resolve_run_data_mode(config)
    if mode != "embeddings":
        return
    from uqlab_core.models.backbones.dinov2_backbone import assert_dinov2_weights_available

    assert_dinov2_weights_available(config.model.dinov2_model)


def step2_materialize_tensor_packs(
    config: ExperimentConfig,
    ctx: ExperimentDataContext,
    *,
    device: torch.device,
    feature_cache_dir: Path,
    feature_batch_size: int,
) -> dict[str, Any]:
    """Compat alias — prefer :func:`build_run_data`."""
    _assert_dinov2_if_needed(config, device)
    return prepare_run_data_context(
        config=config,
        dataset=ctx.dataset,
        split_spec=ctx.split_spec,
        dataset_name=ctx.dataset_name,
        device=device,
        feature_cache_dir=feature_cache_dir,
        noise_type=ctx.noise_type,
        feature_batch_size=feature_batch_size,
    )


def build_run_data(
    config: ExperimentConfig,
    project_root: Path,
    *,
    seed: int,
    device: torch.device | None = None,
    feature_cache_dir: Path | None = None,
    feature_batch_size: int | None = None,
) -> RunDataBundle:
    """
    **Start here.** YAML config → dataset, splits, and train/eval tensor packs.

    Replaces the old two-call sequence
    ``prepare_experiment_data`` + ``prepare_run_data_context``.

    Pass ``feature_batch_size=extract_run_config(config).feature_batch_size`` when
    available so feature extraction matches the run's training config.
    """
    from uqlab_core.shared.utils.classification import auto_device

    ctx = step1_load_dataset_and_splits(config, project_root, seed=seed)
    if ctx.request is None:
        raise RuntimeError("step1 did not attach PilotDataRequest to ExperimentDataContext")
    dev = device or auto_device()
    cache = feature_cache_dir or (project_root / config.paths.feature_cache_dir)
    # Prefer explicit run_cfg.feature_batch_size; avoid reading config.training here.
    batch = feature_batch_size if feature_batch_size is not None else TrainingConfig().feature_batch_size
    _assert_dinov2_if_needed(config, dev)
    data_pack = prepare_run_data_context(
        config=config,
        dataset=ctx.dataset,
        split_spec=ctx.split_spec,
        dataset_name=ctx.dataset_name,
        device=dev,
        feature_cache_dir=cache,
        noise_type=ctx.noise_type,
        feature_batch_size=batch,
    )
    return RunDataBundle(
        dataset=ctx.dataset,
        split_spec=ctx.split_spec,
        data_pack=data_pack,
        request=ctx.request,
        ctx=ctx,
    )


__all__ = [
    "CIFAR10NImageDataset",
    "ClassificationImageDataset",
    "EVAL_PACK_KEYS",
    "ExperimentDataContext",
    "PilotDataRequest",
    "RunDataBundle",
    "RunDataMode",
    "RunDataPacks",
    "build_run_data",
    "get_data_loading_mode",
    "get_dataset_image_transform",
    "load_image_datasets",
    "prepare_eval_data",
    "prepare_eval_tensors",
    "prepare_experiment_data",
    "prepare_run_data_context",
    "resolve_run_data_mode",
    "step1_load_dataset_and_splits",
    "step2_materialize_tensor_packs",
]
