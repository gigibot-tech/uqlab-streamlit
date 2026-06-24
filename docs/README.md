# UQLab Streamlit Documentation

Welcome to the UQLab Streamlit documentation. This directory contains comprehensive documentation organized by category for easy navigation.

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

### ✨ [Features](./features/)
Feature documentation and user guides:
- [Sweep Grouping](./features/sweep-grouping.md) - Experiment sweep grouping functionality

### 🔍 [Troubleshooting](./troubleshooting/)
Bug fixes, issues, and debugging guides:
- [ResNet Feature Extractor Fix](./troubleshooting/resnet-feature-extractor.md) - ResNet training mode issues
- [Progressive UI Fixes](./troubleshooting/progressive-ui.md) - UI component improvements
- [Startup Issues](./troubleshooting/startup-issues.md) - Application startup problems

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

**Machine Learning**
- [ResNet Feature Extractor Fix](./troubleshooting/resnet-feature-extractor.md)
- [Sweep Grouping](./features/sweep-grouping.md)

**UI & Frontend**
- [Progressive UI Fixes](./troubleshooting/progressive-ui.md)
- [Startup Issues](./troubleshooting/startup-issues.md)

**Development Tools**
- [UV & Ruff Setup](./setup/uv-ruff.md)

### By Date (Most Recent First)

1. [Startup Issues](./troubleshooting/startup-issues.md)
2. [Progressive UI Fixes](./troubleshooting/progressive-ui.md)
3. [Sweep Grouping](./features/sweep-grouping.md)
4. [ResNet Feature Extractor Fix](./troubleshooting/resnet-feature-extractor.md)
5. [MinIO Implementation](./architecture/minio-storage.md)
6. [MinIO Setup](./setup/minio.md)
7. [UV & Ruff Setup](./setup/uv-ruff.md)

## 📝 Documentation Guidelines

### For Contributors

When adding new documentation:

1. **Choose the right category**:
   - `setup/` - Installation and configuration
   - `architecture/` - Design and technical decisions
   - `features/` - User-facing functionality
   - `troubleshooting/` - Bug fixes and issues
   - `api/` - API reference
   - `deployment/` - Deployment and infrastructure
   - `development/` - Development workflows

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

*Last updated: 2026-06-18*
