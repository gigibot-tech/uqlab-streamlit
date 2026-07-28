# Test Configs

Small YAML experiment configs used to smoke-test each supported architecture.

These files were relocated from `configs/test/` so that test-related assets live
under `tests/` instead of the root `configs/` tree.

## Files

- `test_cnn_mcdropout.yaml` – CNN MC Dropout smoke test
- `test_dinov2_mlp.yaml` – DINOv2 + MLP smoke test
- `test_resnet18_mcdropout.yaml` – ResNet18 MC Dropout smoke test

## Usage

Run the architecture validation script from the repository root:

```bash
python scripts/setup/validate_architectures.py
```

Or run a single config directly with the CLI:

```bash
python scripts/run_fast_uncertainty_classification.py \
    tests/configs/test_cnn_mcdropout.yaml \
    /tmp/test_cnn_mcdropout
```
