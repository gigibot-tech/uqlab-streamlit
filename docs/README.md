# UQLab Streamlit Documentation

Welcome to the UQLab Streamlit documentation. This directory contains comprehensive documentation organized by category for easy navigation.

> **Note:** The `docs/features/` folder has been retired. Its contents were small, topic-specific docs that now live under `signals/`, `validation/`, `streamlit/`, `user-guides/`, `troubleshooting/`, and `architecture/`. See the category sections below or the [relocation index](./features/README.md).

## 📚 Documentation Structure

### 🔧 [Setup](./setup/)
Installation, configuration, and environment setup guides:
- [MinIO Setup](./setup/minio.md) - MinIO object storage configuration
- [UV & Ruff Setup](./setup/uv-ruff.md) - Modern Python tooling setup

### 🏗️ [Architecture](./architecture/)
System design, patterns, and technical decisions:
- **[UQLab flow](./UQLAB_FLOW.md)** — canonical: experiments, fit/predict, signal_table, disentanglement
- [uq-flow.md](./architecture/uq-flow.md) — redirect only
- [MinIO Storage Implementation](./architecture/minio-storage.md) - Object storage architecture
- [Paper API → UQLab mapping](./architecture/PAPER_FLOW.md) - full run API map

### 📡 [Signals](./signals/)
Uncertainty signal registry, metrics, and attribution artifacts:
- [Signal Registry](./signals/signal-registry.md) - EK-FAK pipeline and metric cookbook
- [Registries](./signals/registries.md) - METRICS, SOURCE_REGISTRY, perspectives, models
- [Attribution Artifacts](./signals/ATTRIBUTION_ARTIFACTS.md) - `zwischen/` influence matrices

### ✅ [Validation](./validation/)
Experiment validation, sweeps, benchmarks, and four-region partition:
- [Evaluation Pipeline](./validation/evaluation-pipeline.md) - YAML → train → signals → artifacts
- [Evaluation Protocol](./validation/evaluation-protocol.md) - current vs 4-region evaluation
- [Validation Sweeps](./validation/validation-sweeps.md) - noise/sparsity sweep grids
- [Disentanglement Benchmark](./validation/disentanglement-benchmark.md) - paper metric + campaign plots
- [Four-Region Partition](./validation/four-region-partition.md) - data layer split/noise
- [Four-Region Notebook](./validation/four-region-notebook.md) - six-step benchmark notebook
- [Sweep Grouping](./validation/sweep-grouping.md) - post-run campaign grouping

### 📖 [User Guides](./user-guides/)
Hands-on guides for data, workflow, and plugins:
- [Data Pipeline](./user-guides/data-pipeline.md) - `build_run_data` walkthrough
- [Dataset Plugin](./user-guides/dataset-plugin.md) - adding datasets via registry
- [Workflow Config](./user-guides/workflow-config.md) - wizard → YAML field mapping

### 🖥️ [Streamlit](./streamlit/)
Streamlit UI components, debug surfaces, and app guides:
- [UI Debug](./streamlit/ui-debug.md) - progressive app debug surfaces
- [Checkpoint Arsenal](./streamlit/checkpoint-arsenal.md) - Step 2.5 checkpoint review
- [Streamlit README](./streamlit/STREAMLIT_README.md) - app overview

### 🔍 [Troubleshooting](./troubleshooting/)
Bug fixes, issues, and debugging guides:
- [ResNet Feature Extractor Fix](./troubleshooting/resnet-feature-extractor.md) - ResNet training mode issues
- [Progressive UI Fixes](./troubleshooting/progressive-ui.md) - UI component improvements
- [Startup Issues](./troubleshooting/startup-issues.md) - Application startup problems
- [Run Recovery](./troubleshooting/run-recovery.md) - finalize failed runs from disk

### 🔌 [API](./api/)
API documentation, endpoints, and schemas:
- *Coming soon*

### 🚀 [Deployment](./deployment/)
Deployment guides, CI/CD, and infrastructure:
- *Coming soon*

### 💻 [Development](./development/)
Development workflows and contributing guides:
- *Coming soon*

## 🔍 Quick Navigation

### By Topic

**Storage & Infrastructure**
- [MinIO Setup](./setup/minio.md)
- [MinIO Implementation](./architecture/minio-storage.md)

**Machine Learning & Signals**
- [Signal Registry](./signals/signal-registry.md)
- [Registries](./signals/registries.md)
- [Attribution Artifacts](./signals/ATTRIBUTION_ARTIFACTS.md)
- [ResNet Feature Extractor Fix](./troubleshooting/resnet-feature-extractor.md)

**Validation & Benchmarks**
- [Evaluation Pipeline](./validation/evaluation-pipeline.md)
- [Evaluation Protocol](./validation/evaluation-protocol.md)
- [Validation Sweeps](./validation/validation-sweeps.md)
- [Disentanglement Benchmark](./validation/disentanglement-benchmark.md)
- [Four-Region Partition](./validation/four-region-partition.md)
- [Four-Region Notebook](./validation/four-region-notebook.md)
- [Sweep Grouping](./validation/sweep-grouping.md)

**User Guides**
- [Data Pipeline](./user-guides/data-pipeline.md)
- [Dataset Plugin](./user-guides/dataset-plugin.md)
- [Workflow Config](./user-guides/workflow-config.md)

**UI & Frontend**
- [UI Debug](./streamlit/ui-debug.md)
- [Checkpoint Arsenal](./streamlit/checkpoint-arsenal.md)
- [Progressive UI Fixes](./troubleshooting/progressive-ui.md)
- [Startup Issues](./troubleshooting/startup-issues.md)

**Operations**
- [Run Recovery](./troubleshooting/run-recovery.md)

**Development Tools**
- [UV & Ruff Setup](./setup/uv-ruff.md)

### By Date (Most Recent First)

1. [Startup Issues](./troubleshooting/startup-issues.md)
2. [Progressive UI Fixes](./troubleshooting/progressive-ui.md)
3. [Run Recovery](./troubleshooting/run-recovery.md)
4. [UI Debug](./streamlit/ui-debug.md)
5. [Checkpoint Arsenal](./streamlit/checkpoint-arsenal.md)
6. [Sweep Grouping](./validation/sweep-grouping.md)
7. [ResNet Feature Extractor Fix](./troubleshooting/resnet-feature-extractor.md)
8. [MinIO Implementation](./architecture/minio-storage.md)
9. [MinIO Setup](./setup/minio.md)
10. [UV & Ruff Setup](./setup/uv-ruff.md)

## 📝 Documentation Guidelines

### For Contributors

When adding new documentation:

1. **Choose the right category**:
   - `setup/` - Installation and configuration
   - `architecture/` - Design, paper mappings, and technical decisions
   - `signals/` - Signal registry, metrics, and attribution artifacts
   - `validation/` - Benchmarks, sweeps, four-region partition, evaluation protocol
   - `user-guides/` - Hands-on guides for data, workflow, and plugins
   - `streamlit/` - Streamlit UI components and debug surfaces
   - `troubleshooting/` - Bug fixes, recovery, and debugging guides
   - `api/` - API reference
   - `deployment/` - Deployment and infrastructure
   - `development/` - Development workflows

   Do **not** add new docs under `features/`; that folder is retired.

2. **Follow naming conventions**:
   - Use lowercase with hyphens: `my-feature.md`
   - Be descriptive but concise
   - Avoid redundant prefixes (category is in path)

3. **Update this index**:
   - Add your document to the appropriate section
   - Include a brief description
   - Update the "By Date" section

4. **Use consistent formatting**:
   - Start with a clear title (H1)
   - Include a brief overview
   - Use sections and subsections
   - Add code examples where relevant
   - Include links to related docs

### Documentation Standards

- **Clear and concise**: Write for your audience
- **Well-structured**: Use headings and sections
- **Code examples**: Include practical examples
- **Up-to-date**: Keep documentation current
- **Cross-referenced**: Link to related docs

## 🔗 Related Resources

- [Main README](../README.md) - Project overview and quick start
- [GitHub Issues](../GITHUB_ISSUES.md) - Known issues and tracking
- [Changelog](../CHANGELOG.md) - Version history (if available)

## 📧 Need Help?

If you can't find what you're looking for:
1. Check the [Troubleshooting](./troubleshooting/) section
2. Search the documentation using your editor's search
3. Check the main [README](../README.md)
4. Open an issue on GitHub

---

*Last updated: 2026-10-10*
