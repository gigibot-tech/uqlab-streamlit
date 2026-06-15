"""
Experiment management with py-experimenter integration.

Provides graceful degradation from MySQL-backed experiment tracking
to simple YAML + JSON file-based tracking.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import json
import yaml
from datetime import datetime

# Check for py-experimenter
try:
    from py_experimenter.experimenter import PyExperimenter
    from py_experimenter.result_processor import ResultProcessor
    PY_EXPERIMENTER_AVAILABLE = True
except ImportError:
    PY_EXPERIMENTER_AVAILABLE = False
    PyExperimenter = None
    ResultProcessor = None


class ExperimentManager:
    """
    Unified experiment management interface.
    
    Uses py-experimenter if available (MySQL-backed), otherwise falls back
    to simple file-based tracking with YAML configs and JSON results.
    
    Args:
        config_path: Path to experiment configuration file
        database_url: MySQL database URL (optional, for py-experimenter)
        experiment_name: Name of the experiment
        use_database: Whether to use database backend (requires py-experimenter)
    
    Example with py-experimenter:
        >>> manager = ExperimentManager(
        ...     config_path="config.yaml",
        ...     database_url="mysql://user:pass@localhost/experiments",
        ...     experiment_name="uq_classification"
        ... )
        >>> for experiment in manager.get_experiments():
        ...     result = run_experiment(experiment)
        ...     manager.save_result(experiment['id'], result)
    
    Example with file-based fallback:
        >>> manager = ExperimentManager(
        ...     config_path="config.yaml",
        ...     experiment_name="uq_classification",
        ...     use_database=False
        ... )
        >>> config = manager.get_config()
        >>> result = run_experiment(config)
        >>> manager.save_result(None, result)
    """
    
    def __init__(
        self,
        config_path: Path,
        experiment_name: str,
        database_url: Optional[str] = None,
        use_database: bool = True,
    ):
        self.config_path = Path(config_path)
        self.experiment_name = experiment_name
        self.database_url = database_url
        self.use_database = use_database and PY_EXPERIMENTER_AVAILABLE
        
        # Load configuration
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize backend
        if self.use_database and database_url:
            try:
                self.experimenter = PyExperimenter(
                    experiment_configuration_file_path=str(self.config_path),
                    name=experiment_name,
                    database_url=database_url,
                )
                self.backend = 'py-experimenter'
                print(f"✅ Using py-experimenter with database: {database_url}")
            except Exception as e:
                print(f"⚠️  Failed to initialize py-experimenter: {e}")
                print("   Falling back to file-based tracking...")
                self.experimenter = None
                self.backend = 'file'
        else:
            self.experimenter = None
            self.backend = 'file'
            if not PY_EXPERIMENTER_AVAILABLE:
                print("⚠️  py-experimenter not installed. Using file-based tracking.")
            else:
                print("✅ Using file-based tracking (no database configured)")
        
        # Setup results directory for file-based backend
        if self.backend == 'file':
            self.results_dir = self.config_path.parent / 'results' / experiment_name
            self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def get_config(self) -> Dict[str, Any]:
        """Get experiment configuration."""
        return self.config
    
    def get_experiments(self):
        """
        Get experiments to run.
        
        With py-experimenter: yields experiment configurations from database
        With file backend: yields single configuration from YAML
        """
        if self.backend == 'py-experimenter' and self.experimenter:
            # Get experiments from database
            for experiment in self.experimenter.execute():
                yield experiment
        else:
            # Single experiment from config file
            yield {
                'id': f"{self.experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'config': self.config
            }
    
    def save_result(
        self,
        experiment_id: Optional[str],
        results: Dict[str, Any],
        status: str = 'done'
    ) -> None:
        """
        Save experiment results.
        
        Args:
            experiment_id: Experiment ID (from py-experimenter) or None
            results: Dictionary of results to save
            status: Experiment status ('done', 'error', etc.)
        """
        if self.backend == 'py-experimenter' and self.experimenter:
            # Save to database
            try:
                self.experimenter.process_results(
                    experiment_id=experiment_id,
                    result_dict=results,
                    status=status
                )
                print(f"✅ Results saved to database (experiment_id: {experiment_id})")
            except Exception as e:
                print(f"⚠️  Failed to save to database: {e}")
                print("   Saving to file as fallback...")
                self._save_to_file(experiment_id, results, status)
        else:
            # Save to file
            self._save_to_file(experiment_id, results, status)
    
    def _save_to_file(
        self,
        experiment_id: Optional[str],
        results: Dict[str, Any],
        status: str
    ) -> None:
        """Save results to JSON file."""
        if experiment_id is None:
            experiment_id = f"{self.experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result_file = self.results_dir / f"{experiment_id}.json"
        
        output = {
            'experiment_id': experiment_id,
            'experiment_name': self.experiment_name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'results': results
        }
        
        with open(result_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✅ Results saved to: {result_file}")
    
    def get_all_results(self):
        """
        Retrieve all experiment results.
        
        With py-experimenter: queries database
        With file backend: reads JSON files
        """
        if self.backend == 'py-experimenter' and self.experimenter:
            # Query database
            processor = ResultProcessor(self.experimenter)
            return processor.get_results()
        else:
            # Read JSON files
            results = []
            for result_file in self.results_dir.glob('*.json'):
                with open(result_file, 'r') as f:
                    results.append(json.load(f))
            return results


def print_py_experimenter_instructions() -> None:
    """Print py-experimenter setup instructions."""
    print("\n" + "="*70)
    print("🔬 py-experimenter Setup Instructions")
    print("="*70)
    print("\n1. Install py-experimenter:")
    print("   pip install py-experimenter mysql-connector-python")
    print("\n2. Setup MySQL database:")
    print("   # Using Docker:")
    print("   docker run -d --name mysql-experiments \\")
    print("     -e MYSQL_ROOT_PASSWORD=password \\")
    print("     -e MYSQL_DATABASE=experiments \\")
    print("     -p 3306:3306 mysql:8.0")
    print("\n3. Configure database URL:")
    print("   database_url: 'mysql://root:password@localhost:3306/experiments'")
    print("\n4. Create experiment configuration YAML:")
    print("   See: https://py-experimenter.readthedocs.io/")
    print("\nBenefits:")
    print("  • Centralized experiment tracking across machines")
    print("  • Automatic parameter grid search")
    print("  • Result aggregation and comparison")
    print("  • Experiment status tracking (running/done/error)")
    print("  • Resume interrupted experiments")
    print("\nFallback:")
    print("  • Without py-experimenter: uses YAML + JSON files")
    print("  • All core functionality still works")
    print("="*70 + "\n")


def check_py_experimenter_available() -> bool:
    """Check if py-experimenter is available."""
    return PY_EXPERIMENTER_AVAILABLE


# Made with Bob