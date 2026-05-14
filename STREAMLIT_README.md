# Streamlit Dashboard for Uncertainty Quantification

A lightweight Streamlit frontend that connects to the FastAPI backend to visualize dataset statistics and manage uncertainty quantification experiments.

## Features

- 📊 **Dataset Statistics Dashboard**
  - Total, clean, and noisy sample counts
  - Overall noise rate
  - Per-class noise distribution
  - Interactive visualizations

- 🧪 **Experiment Management** (Coming Soon)
  - Configure and launch experiments
  - View experiment results
  - Compare different uncertainty methods

## Quick Start

### Prerequisites

- Python 3.9+
- FastAPI backend running (see main README)

### Option 1: Using the Run Script (Recommended)

```bash
# Start the backend first
docker-compose up backend

# In a new terminal, run the Streamlit app
./run_streamlit.sh
```

The dashboard will open automatically at http://localhost:8501

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r streamlit_requirements.txt

# Run Streamlit
streamlit run streamlit_app.py
```

## Configuration

### API URL

By default, the app connects to `http://localhost:8000`. To change this:

```bash
export API_URL=http://your-backend-url:8000
./run_streamlit.sh
```

### Authentication (Optional)

If your backend requires authentication:

```bash
export API_TOKEN=your_access_token
./run_streamlit.sh
```

## Usage

1. **Select Dataset**: Choose from available datasets (currently CIFAR-10N)
2. **Choose Noise Type**: Select the type of label noise to analyze
3. **View Statistics**: See overall metrics and per-class noise distribution
4. **Run Experiments**: Configure and launch uncertainty quantification experiments

## Dataset Statistics View

The dashboard displays:

- **Summary Metrics**
  - Total samples in the dataset
  - Number of clean samples
  - Number of noisy samples
  - Overall noise rate percentage

- **Class-Level Analysis**
  - Noise distribution for each class
  - Clean vs noisy sample counts
  - Per-class noise rates
  - Visual bar chart of noise rates

## API Endpoints Used

- `GET /api/v1/datasets/{dataset_name}/stats` - Fetch dataset statistics
- `POST /api/v1/experiments/` - Create new experiment (coming soon)
- `GET /api/v1/experiments/` - List experiments (coming soon)
- `GET /api/v1/experiments/{id}` - Get experiment details (coming soon)

## Troubleshooting

### Backend Connection Issues

If you see "Failed to fetch dataset stats":

1. Ensure the backend is running:
   ```bash
   docker-compose up backend
   ```

2. Check the backend is accessible:
   ```bash
   curl http://localhost:8000/api/v1/datasets/cifar10n/stats?noise_type=worse_label
   ```

3. Verify the API_URL environment variable is correct

### Port Already in Use

If port 8501 is already in use:

```bash
streamlit run streamlit_app.py --server.port 8502
```

## Development

### Adding New Features

The Streamlit app is structured as follows:

- `streamlit_app.py` - Main application file
- `fetch_dataset_stats()` - API communication
- `main()` - Dashboard layout and logic

To add new features:

1. Add API functions for new endpoints
2. Create new UI sections in `main()`
3. Update this README

### Testing

```bash
# Test API connection
python -c "import requests; print(requests.get('http://localhost:8000/api/v1/datasets/cifar10n/stats?noise_type=worse_label').json())"
```

## Comparison with React Frontend

| Feature | Streamlit | React Frontend |
|---------|-----------|----------------|
| Setup Time | < 1 minute | ~5 minutes |
| Dependencies | 3 packages | 50+ packages |
| Hot Reload | ✅ Built-in | ✅ Via Vite |
| Customization | Limited | Full control |
| Best For | Quick testing, prototypes | Production deployment |

## Next Steps

- [ ] Implement experiment creation UI
- [ ] Add experiment results viewer
- [ ] Add real-time training progress
- [ ] Add model comparison charts
- [ ] Export results to CSV/JSON

## Made with Bob