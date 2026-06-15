# UQLab Streamlit

Interactive Streamlit dashboard for uncertainty quantification experiments using the [UQLab framework](https://github.com/gigibot-tech/uqlab).

## 🏗️ Repository Structure

```
uqlab-streamlit/
├── src/
│   └── uqlab/                    # Git submodule: Core ML framework
│       ├── 1_data/               # Data loaders and preprocessing
│       ├── 2_models/             # Model architectures (DINOv2, CNN, ResNet)
│       ├── 3_training/           # Training utilities
│       ├── 4_evaluation/         # Evaluation metrics and signals
│       ├── 5_api/                # API integrations (watsonx.ai)
│       ├── 7_orchestration/      # Experiment orchestration
│       ├── ui_components/        # Reusable Streamlit components
│       └── shared/               # Shared utilities and configs
├── backend/                      # FastAPI backend
│   └── app/
│       ├── api/                  # API routes
│       ├── core/                 # Core backend logic
│       ├── db/                   # Database models
│       └── services/             # Business logic
├── streamlit_app.py              # Main Streamlit dashboard
├── streamlit_app_progressive.py  # Advanced/experimental UI
├── scripts/                      # Utility scripts
├── configs/                      # Experiment configurations
├── notebooks/                    # Jupyter notebooks
├── docker-compose.yml            # Docker orchestration
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Git
- Docker (optional, for backend)

### Installation

#### 1. Clone with Submodule

```bash
# Clone repository with uqlab submodule
git clone --recurse-submodules https://github.com/gigibot-tech/uqlab-streamlit.git
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
pip install -r requirements.txt
```

#### 3. Run Streamlit App

```bash
# Main dashboard
streamlit run streamlit_app.py

# Progressive/advanced UI
streamlit run streamlit_app_progressive.py
```

The app will open in your browser at `http://localhost:8501`

### Optional: Run Backend

```bash
# Using Docker
docker-compose up -d

# Or locally
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend API will be available at `http://localhost:8000`

## 📊 Features

### Model Architectures

- **DINOv2 + MLP**: Fast feature-space training with pretrained vision transformer
- **Custom CNN**: End-to-end training with MC Dropout
- **ResNet18**: Both feature-space and end-to-end modes with MC Dropout

### Uncertainty Quantification

- **MC Dropout**: Multiple forward passes for uncertainty estimation
- **20+ Uncertainty Signals**: Entropy, mutual information, variance, etc.
- **Data Attribution**: DualXDA for gradient-based attribution
- **Calibration**: Temperature scaling and Platt scaling

### Experiment Management

- **Single Experiments**: Configure and run individual experiments
- **Batch Experiments**: Parameter sweeps with automatic orchestration
- **Real-time Monitoring**: Live results and metrics visualization
- **Result Storage**: PostgreSQL backend with experiment tracking

### Datasets

- **CIFAR-10N**: CIFAR-10 with synthetic label noise
  - `worse_label`: 18% noise
  - `random_label1-3`: Various noise patterns
  - `aggre_label`: Aggregated annotations
- **CIFAR-10**: Clean version
- **Custom**: Easy to add new datasets

## 🔧 Configuration

### Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit with your settings
# - Database credentials
# - API keys (watsonx.ai, etc.)
# - Feature flags
```

### Key Configuration Files

- `.env`: Main environment variables
- `backend/.env`: Backend-specific settings
- `configs/`: Experiment YAML configurations
- `docker-compose.yml`: Docker services

## 🧪 Running Experiments

### Via Streamlit UI

1. **Configure Dataset**: Select CIFAR-10N and noise type
2. **Configure Model**: Choose architecture and training mode
3. **Configure Training**: Set epochs, learning rate, batch size
4. **Configure Evaluation**: Select uncertainty signals and metrics
5. **Run Experiment**: Click "Create Experiment" and monitor results

### Via Python API

```python
from uqlab.shared.config.classification import ModelConfig
from uqlab.7_orchestration.experiment_runner import run_experiment

# Configure experiment
config = ModelConfig(
    architecture="resnet18_mcdropout",
    training_mode="feature_space",  # or "end_to_end"
    dropout=0.3,
    hidden_dim=256
)

# Run experiment
results = run_experiment(config)
```

### Batch Experiments

```python
from backend.app.services.batch_service import create_batch_experiment

# Create batch with parameter sweep
batch = create_batch_experiment(
    name="dropout_sweep",
    base_config=config,
    sweep_parameter="dropout",
    sweep_values=[0.1, 0.2, 0.3, 0.4, 0.5]
)
```

## 📚 Documentation

- **UQLab Core**: `src/uqlab/README.md`
- **Model Architectures**: `src/uqlab/2_models/README.md`
- **API Documentation**: http://localhost:8000/docs (when backend running)
- **Architecture Guide**: `docs/architecture/ARCHITECTURE_GUIDE.md`
- **Quick Start Guide**: `QUICK_START_GUIDE.md`

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

## 🔄 Submodule Management

### Update UQLab Core

```bash
cd src/uqlab
git pull origin main
cd ../..
git add src/uqlab
git commit -m "Update uqlab submodule"
git push
```

### Switch UQLab Branch

```bash
cd src/uqlab
git checkout feature-branch
cd ../..
git add src/uqlab
git commit -m "Switch uqlab to feature-branch"
git push
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

## 🐛 Troubleshooting

### Submodule Issues

```bash
# If submodule is empty
git submodule update --init --recursive

# If submodule is out of sync
git submodule update --remote --merge
```

### Import Errors

```bash
# Reinstall uqlab in editable mode
pip install -e src/uqlab
```

### Database Connection

```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres
```

## 📝 License

[Your License Here]

## 🙏 Acknowledgments

- **UQLab Core**: https://github.com/gigibot-tech/uqlab
- **DINOv2**: Meta AI Research
- **CIFAR-10N**: Wei et al., 2022
- **MC Dropout**: Gal & Ghahramani, 2016

## 📧 Contact

- **Issues**: https://github.com/gigibot-tech/uqlab-streamlit/issues
- **UQLab Issues**: https://github.com/gigibot-tech/uqlab/issues
- **Email**: your-email@example.com

---

**Version**: 1.0.0  
**Last Updated**: 2026-06-15  
**Status**: Production Ready ✅
