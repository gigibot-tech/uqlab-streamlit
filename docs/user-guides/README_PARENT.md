# UQLab-CEN: Uncertainty Quantification Platform

Complete uncertainty quantification platform with Streamlit UI, FastAPI backend, and the UQLab core framework.

## 🏗️ Repository Structure

```
uqlab-streamlit/
├── src/
│   └── uqlab/                    # Core UQ framework (Git submodule)
│       ├── 1_data/               # Data loaders and preprocessing
│       ├── 2_models/             # Model architectures
│       ├── 3_training/           # Training utilities
│       ├── 4_evaluation/         # Evaluation and metrics
│       ├── 5_api/                # API integrations
│       ├── 7_orchestration/      # Experiment orchestration
│       ├── ui_components/        # Reusable UI components
│       └── ...
├── backend/                      # FastAPI backend
│   └── app/
│       ├── api/                  # API routes
│       ├── core/                 # Core backend logic
│       ├── db/                   # Database models
│       └── services/             # Business logic
├── streamlit_app.py              # Main Streamlit dashboard
├── streamlit_app_progressive.py  # Progressive/advanced UI
├── scripts/                      # Utility scripts
├── configs/                      # Configuration files
├── notebooks/                    # Jupyter notebooks
└── docker-compose.yml            # Docker orchestration
```

## 📦 Components

### 1. **UQLab Core** (Submodule)
- **Repository**: https://github.com/gigibot-tech/uqlab.git
- **Purpose**: Core uncertainty quantification framework
- **Key Features**:
  - Model architectures (DINOv2, CNN, ResNet18 with MC Dropout)
  - Feature extraction and uncertainty quantification
  - Data loaders for CIFAR-10N and other datasets
  - Evaluation metrics and signal computation
  - Reusable UI components

### 2. **Streamlit Frontend**
- **Main App** (`streamlit_app.py`): Production-ready dashboard
- **Progressive App** (`streamlit_app_progressive.py`): Advanced features and experiments
- **Features**:
  - Interactive experiment configuration
  - Real-time results visualization
  - Batch experiment management
  - Signal analysis and validation

### 3. **FastAPI Backend**
- **Location**: `backend/`
- **Features**:
  - RESTful API for experiment management
  - Database integration (PostgreSQL)
  - Batch experiment orchestration
  - Authentication and authorization
  - watsonx.ai integration

### 4. **Orchestration**
- **Location**: `src/uqlab/7_orchestration/`
- **Features**:
  - Experiment runner
  - Batch experiment runner
  - Checkpoint management
  - Result storage and retrieval

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.10+
python --version

# Docker (optional, for backend)
docker --version
```

### Installation

#### 1. Clone with Submodules
```bash
git clone --recurse-submodules https://github.com/YOUR_ORG/uqlab-streamlit.git
cd uqlab-streamlit

# If you already cloned without submodules:
git submodule update --init --recursive
```

#### 2. Install Dependencies
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install UQLab core
pip install -e src/uqlab

# Install Streamlit requirements
pip install -r streamlit_requirements.txt

# Install backend requirements (if running locally)
pip install -r backend/requirements.txt
```

#### 3. Run Streamlit App
```bash
# Main dashboard
streamlit run streamlit_app.py

# Progressive/advanced UI
streamlit run streamlit_app_progressive.py
```

#### 4. Run Backend (Optional)
```bash
# Using Docker
docker-compose up -d

# Or locally
cd backend
uvicorn app.main:app --reload
```

## 📖 Documentation

### UQLab Core
- **Main README**: `src/uqlab/README.md`
- **Models Documentation**: `src/uqlab/2_models/README.md`
- **API Documentation**: `src/uqlab/5_api/README.md`

### Streamlit Apps
- **Main App Guide**: `STREAMLIT_ARCHITECTURE_CLARIFIED.md`
- **Progressive App**: `PROGRESSIVE_APP_README.md`
- **Quick Start**: `QUICK_START_GUIDE.md`

### Backend
- **API Documentation**: http://localhost:8000/docs (when running)
- **Architecture**: `ARCHITECTURE_DIAGRAM.md`

## 🔧 Configuration

### Environment Variables
```bash
# Copy example files
cp .env.example .env
cp backend/.env.example backend/.env

# Edit with your settings
# - Database credentials
# - API keys (watsonx.ai, etc.)
# - Feature flags
```

### Key Configuration Files
- `.env`: Main environment variables
- `backend/.env`: Backend-specific settings
- `configs/`: Experiment configurations
- `docker-compose.yml`: Docker services

## 🧪 Running Experiments

### Single Experiment (Streamlit)
1. Open `streamlit_app.py`
2. Configure dataset, model, and training parameters
3. Click "Create Experiment"
4. Monitor results in real-time

### Batch Experiments (Streamlit)
1. Switch to "Batch Experiments" tab
2. Select parameter to sweep
3. Configure sweep range
4. Submit batch
5. View aggregated results

### Programmatic (Python)
```python
from uqlab.shared.config.classification import ModelConfig
from uqlab.7_orchestration.experiment_runner import run_experiment

# Configure experiment
config = ModelConfig(
    architecture="resnet18_mcdropout",
    training_mode="feature_space",
    dropout=0.3
)

# Run experiment
results = run_experiment(config)
```

## 🔬 Key Features

### Model Architectures
- **DINOv2 + MLP**: Fast feature-space training
- **Custom CNN**: End-to-end training from scratch
- **ResNet18**: Both feature-space and end-to-end modes ⭐

### Uncertainty Quantification
- **MC Dropout**: Multiple forward passes for uncertainty
- **Deep Ensembles**: Multiple model training
- **Calibration**: Temperature scaling and Platt scaling

### Data Attribution
- **DualXDA**: Gradient-based attribution
- **Influence Functions**: Training data influence
- **Axiom Validation**: Three-axiom framework

### Evaluation Metrics
- **AUROC**: Area under ROC curve
- **ECE**: Expected calibration error
- **Brier Score**: Probabilistic accuracy
- **Custom Signals**: 20+ uncertainty signals

## 📊 Datasets

### Supported Datasets
- **CIFAR-10N**: CIFAR-10 with synthetic label noise
  - `worse_label`: 18% noise
  - `random_label1-3`: Various noise patterns
  - `aggre_label`: Aggregated annotations
- **CIFAR-10**: Clean version
- **Custom**: Easy to add new datasets

### Dataset Configuration
```python
from uqlab.data_loaders.cifar10n_loader import CIFAR10NDataset

dataset = CIFAR10NDataset(
    root="./data",
    noise_type="worse_label",
    train=True,
    download=True
)
```

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Services
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:8501
- **Database**: PostgreSQL on port 5432
- **MLflow** (optional): http://localhost:5000

## 🧩 Submodule Management

### Update UQLab Core
```bash
cd src/uqlab
git pull origin main
cd ../..
git add src/uqlab
git commit -m "Update uqlab submodule"
```

### Switch UQLab Branch
```bash
cd src/uqlab
git checkout feature-branch
cd ../..
git add src/uqlab
git commit -m "Switch uqlab to feature-branch"
```

### Contribute to UQLab
```bash
cd src/uqlab
# Make changes
git add .
git commit -m "Your changes"
git push origin main
cd ../..
git submodule update --remote
```

## 🤝 Contributing

### Development Workflow
1. Create feature branch
2. Make changes
3. Run tests: `pytest tests/`
4. Update documentation
5. Submit pull request

### Code Style
```bash
# Format code
black .
isort .

# Type checking
mypy src/

# Linting
flake8 src/
```

## 📝 License

[Your License Here]

## 🙏 Acknowledgments

- **DINOv2**: Meta AI Research
- **CIFAR-10N**: Wei et al., 2022
- **MC Dropout**: Gal & Ghahramani, 2016
- **DualXDA**: [Citation]

## 📧 Contact

- **Issues**: https://github.com/YOUR_ORG/uqlab-streamlit/issues
- **Email**: your-email@example.com
- **Documentation**: https://your-docs-site.com

---

**Version**: 1.0.0  
**Last Updated**: 2026-06-15  
**Status**: Production Ready ✅