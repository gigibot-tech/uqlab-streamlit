"""Example workflow demonstrating training and Streamlit dashboard usage.

This script shows the complete workflow:
1. Train a model with checkpoints and visualizations
2. Instructions for launching the Streamlit dashboard
3. Example of programmatic data access

Usage:
    python uq_classification/example_streamlit_workflow.py
"""

import subprocess
import sys
from pathlib import Path


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def run_training_example():
    """Run a quick training example to generate data."""
    print_section("Step 1: Training Model with Checkpoints")
    
    print("Running training with visualization enabled...")
    print("This will create experiment data and decision boundary images.\n")
    
    cmd = [
        sys.executable,
        "uq_classification/train_with_checkpoints.py",
        "--experiment-name", "streamlit_demo",
        "--dataset", "synthetic",
        "--n-samples", "500",
        "--n-features", "2",
        "--n-classes", "3",
        "--num-epochs", "20",
        "--checkpoint-freq", "5",
        "--viz-freq", "5",
        "--batch-size", "32",
        "--learning-rate", "0.01"
    ]
    
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("\n✅ Training completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Training failed: {e}")
        return False
    except FileNotFoundError:
        print("\n❌ Training script not found. Make sure you're in the project root.")
        return False


def show_dashboard_instructions():
    """Show instructions for launching the dashboard."""
    print_section("Step 2: Launch Streamlit Dashboard")
    
    print("To explore the results in the interactive dashboard, run:\n")
    print("    streamlit run uq_classification/streamlit_app.py\n")
    print("The dashboard will open in your browser at http://localhost:8501\n")
    print("Features available:")
    print("  • 📊 View training metrics and curves")
    print("  • 🎯 Explore decision boundaries with epoch slider")
    print("  • 🔄 Compare multiple checkpoints side-by-side")
    print("  • 💾 Export data as CSV or JSON")
    print("  • ⚙️ Configure directories and refresh data\n")


def show_programmatic_access():
    """Show example of programmatic data access."""
    print_section("Step 3: Programmatic Data Access (Optional)")
    
    print("You can also access the data programmatically:\n")
    
    code = '''
from uqlab.classification.streamlit_app import (
    load_experiments,
    load_experiment_data,
    extract_metrics_dataframe,
    get_checkpoint_images
)

# Load all experiments
experiments = load_experiments("experiments")
print(f"Available experiments: {list(experiments.keys())}")

# Load specific experiment
if "streamlit_demo" in experiments:
    run_id = experiments["streamlit_demo"][0]  # Latest run
    data = load_experiment_data("streamlit_demo", run_id)
    
    # Access data
    print(f"\\nRun ID: {data['run_id']}")
    print(f"Parameters: {data['params']}")
    
    # Convert metrics to DataFrame
    df = extract_metrics_dataframe(data['metrics'])
    print(f"\\nMetrics DataFrame:\\n{df.head()}")
    
    # Get checkpoint images
    images = get_checkpoint_images("streamlit_demo", run_id)
    print(f"\\nFound {len(images)} checkpoint visualizations")
'''
    
    print(code)


def check_dependencies():
    """Check if required dependencies are installed."""
    print_section("Checking Dependencies")
    
    required = {
        'streamlit': 'Streamlit dashboard',
        'pandas': 'Data manipulation',
        'PIL': 'Image loading (Pillow)',
        'numpy': 'Numerical operations',
        'matplotlib': 'Plotting',
        'torch': 'PyTorch (for training)'
    }
    
    missing = []
    
    for module, description in required.items():
        try:
            __import__(module)
            print(f"✅ {description:30s} - Installed")
        except ImportError:
            print(f"❌ {description:30s} - Missing")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("\nInstall with:")
        print("    pip install -r uq_classification/requirements_viz.txt\n")
        return False
    else:
        print("\n✅ All dependencies installed!\n")
        return True


def show_directory_structure():
    """Show expected directory structure."""
    print_section("Expected Directory Structure")
    
    structure = """
project_root/
├── experiments/
│   └── streamlit_demo/
│       └── YYYYMMDD_HHMMSS.json    # Experiment data
├── visualizations/
│   └── streamlit_demo/
│       └── YYYYMMDD_HHMMSS/
│           ├── epoch_5.png          # Decision boundaries
│           ├── epoch_10.png
│           ├── epoch_15.png
│           └── epoch_20.png
└── uq_classification/
    ├── streamlit_app.py             # Dashboard app
    ├── train_with_checkpoints.py    # Training script
    └── ...
"""
    
    print(structure)
    
    # Check if directories exist
    exp_dir = Path("experiments/streamlit_demo")
    viz_dir = Path("visualizations/streamlit_demo")
    
    if exp_dir.exists():
        json_files = list(exp_dir.glob("*.json"))
        print(f"✅ Found {len(json_files)} experiment file(s) in {exp_dir}")
    else:
        print(f"ℹ️  Experiment directory will be created: {exp_dir}")
    
    if viz_dir.exists():
        run_dirs = [d for d in viz_dir.iterdir() if d.is_dir()]
        print(f"✅ Found {len(run_dirs)} visualization run(s) in {viz_dir}")
    else:
        print(f"ℹ️  Visualization directory will be created: {viz_dir}")


def main():
    """Main workflow execution."""
    print("\n" + "=" * 70)
    print("  🚀 UQ Classification - Streamlit Dashboard Workflow")
    print("=" * 70)
    
    # Check dependencies
    if not check_dependencies():
        print("\n⚠️  Please install missing dependencies before continuing.")
        return
    
    # Show directory structure
    show_directory_structure()
    
    # Ask user if they want to run training
    print_section("Training Options")
    print("Would you like to:")
    print("  1. Run training example (creates demo data)")
    print("  2. Skip training (use existing data)")
    print("  3. Exit")
    
    try:
        choice = input("\nEnter choice (1/2/3): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\nExiting...")
        return
    
    if choice == "1":
        success = run_training_example()
        if not success:
            print("\n⚠️  Training failed. You can still launch the dashboard if you have existing data.")
    elif choice == "2":
        print("\n✅ Skipping training. Using existing data.")
    else:
        print("\nExiting...")
        return
    
    # Show dashboard instructions
    show_dashboard_instructions()
    
    # Show programmatic access
    show_programmatic_access()
    
    # Final instructions
    print_section("Next Steps")
    print("1. Launch the dashboard:")
    print("   streamlit run uq_classification/streamlit_app.py\n")
    print("2. Select 'streamlit_demo' experiment from the sidebar\n")
    print("3. Explore the interactive visualizations!\n")
    print("4. Try comparing different checkpoints\n")
    print("5. Export data for further analysis\n")
    
    print("=" * 70)
    print("  📚 For more information, see:")
    print("     uq_classification/STREAMLIT_APP_README.md")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

# Made with Bob