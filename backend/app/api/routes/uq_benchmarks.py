"""
UQ Benchmarks API Routes

New endpoints for running uncertainty quantification benchmarks
using the uq_benchmarks package.
"""

import logging
import uuid
from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import SessionDep, CurrentUser
from app.tables import UncertaintyExperiment, JobStatus, User, BenchmarkResult, BenchmarkSweep

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class BenchmarkMethodConfig(BaseModel):
    """Configuration for a UQ method."""
    method_name: str = Field(..., description="UQ method: 'gaussian_logits', 'information_theoretic', 'dualxda'")
    num_samples: int = Field(20, description="Number of MC samples for uncertainty estimation")


class BenchmarkDatasetConfig(BaseModel):
    """Configuration for dataset manipulation."""
    dataset_name: str = Field("cifar10", description="Dataset name")
    test_mode: bool = Field(False, description="Use smaller dataset for quick testing")
    
    # Epistemic uncertainty manipulation
    under_supported_classes: List[int] = Field(default_factory=lambda: [3, 5], description="Classes to under-support")
    under_train_per_class: int = Field(50, description="Training samples per under-supported class")
    regular_train_per_class: int = Field(300, description="Training samples per regular class")
    eval_per_class: int = Field(100, description="Test samples per class")
    
    # Aleatoric uncertainty manipulation
    noise_rate: float = Field(0.0, ge=0.0, le=1.0, description="Label noise rate (0.0 to 1.0)")
    seed: int = Field(42, description="Random seed for reproducibility")


class BenchmarkTrainingConfig(BaseModel):
    """Training configuration."""
    epochs: int = Field(10, ge=1, le=100, description="Number of training epochs")
    batch_size: int = Field(32, ge=1, le=512, description="Batch size")
    verbose: int = Field(1, ge=0, le=2, description="Training verbosity")


class SingleBenchmarkRequest(BaseModel):
    """Request to run a single benchmark experiment."""
    name: str = Field(..., min_length=1, max_length=255, description="Experiment name")
    description: str = Field("", max_length=1000, description="Experiment description")
    
    method: BenchmarkMethodConfig
    dataset: BenchmarkDatasetConfig
    training: BenchmarkTrainingConfig


class LabelNoiseSweepRequest(BaseModel):
    """Request to run label noise sweep benchmark."""
    name: str = Field(..., min_length=1, max_length=255, description="Benchmark name")
    description: str = Field("Label noise sweep benchmark", max_length=1000)
    
    method: BenchmarkMethodConfig
    dataset: BenchmarkDatasetConfig  # Base config, noise_rate will be swept
    training: BenchmarkTrainingConfig
    
    noise_rates: List[float] = Field(
        default_factory=lambda: [0.0, 0.2, 0.4, 0.6, 0.8],
        description="Noise rates to sweep"
    )


class BenchmarkResponse(BaseModel):
    """Response from benchmark execution."""
    id: str
    name: str
    status: str
    method_name: str
    accuracy: float | None = None
    aleatoric_uncertainty: float | None = None
    epistemic_uncertainty: float | None = None
    created_at: datetime
    message: str = ""


class BenchmarkResultsResponse(BaseModel):
    """Response with benchmark sweep results."""
    id: str
    name: str
    method_name: str
    parameter_name: str
    parameter_values: List[float]
    accuracies: List[float]
    aleatoric_uncertainties: List[float]
    epistemic_uncertainties: List[float]


    created_at: datetime


class AvailableMethodsResponse(BaseModel):
    """Response listing available UQ methods."""
    methods: List[dict]


# ============================================================================
# Helper Functions
# ============================================================================

def _check_uq_benchmarks_available():
    """Check if uq_benchmarks package is available."""
    try:
        import uq_benchmarks
        return True
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="UQ Benchmarks package not available. Install with: pip install -e uq_benchmarks/[keras]"
        )


def _get_method(method_name: str, num_samples: int):
    """Get UQ method instance."""
    from uq_benchmarks.models import GAUSSIAN_LOGITS_AVAILABLE
    
    if method_name == "gaussian_logits":
        if not GAUSSIAN_LOGITS_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Gaussian Logits method requires Keras. Install with: pip install keras tensorflow"
            )
        from uq_benchmarks.models.gaussian_logits import create_gaussian_logits_method
        return create_gaussian_logits_method(num_samples=num_samples)
    
    elif method_name == "information_theoretic":
        raise HTTPException(
            status_code=501,
            detail="Information-Theoretic method not yet implemented"
        )
    
    elif method_name == "dualxda":
        raise HTTPException(
            status_code=501,
            detail="DualXDA adapter not yet implemented"
        )
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown method: {method_name}. Available: gaussian_logits"
        )


def _load_dataset(config: BenchmarkDatasetConfig):
    """Load dataset based on configuration."""
    from uq_benchmarks.data.cifar10 import get_cifar10_with_epistemic_manipulation
    
    if config.dataset_name != "cifar10":
        raise HTTPException(
            status_code=400,
            detail=f"Dataset {config.dataset_name} not yet supported. Available: cifar10"
        )
    
    return get_cifar10_with_epistemic_manipulation(
        under_supported_classes=config.under_supported_classes,
        under_train_per_class=config.under_train_per_class,
        regular_train_per_class=config.regular_train_per_class,
        eval_per_class=config.eval_per_class,
        noise_rate=config.noise_rate,
        seed=config.seed
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/methods", response_model=AvailableMethodsResponse)
async def list_available_methods() -> Any:
    """
    List available UQ methods.
    
    Returns information about which methods are available and their requirements.
    """
    _check_uq_benchmarks_available()
    
    from uq_benchmarks.models import GAUSSIAN_LOGITS_AVAILABLE
    
    methods = [
        {
            "name": "gaussian_logits",
            "display_name": "Gaussian Logits",
            "description": "Two-head architecture for disentangled uncertainty",
            "framework": "keras",
            "available": GAUSSIAN_LOGITS_AVAILABLE,
            "requirements": "keras, tensorflow"
        },
        {
            "name": "information_theoretic",
            "display_name": "Information-Theoretic",
            "description": "MI/EE/PE decomposition",
            "framework": "keras",
            "available": False,
            "requirements": "keras, tensorflow (not yet implemented)"
        },
        {
            "name": "dualxda",
            "display_name": "DualXDA",
            "description": "Attribution-based uncertainty signals",
            "framework": "pytorch",
            "available": False,
            "requirements": "torch, torchvision (not yet implemented)"
        }
    ]
    
    return AvailableMethodsResponse(methods=methods)


@router.post("/single", response_model=BenchmarkResponse)
async def run_single_benchmark(
    request: SingleBenchmarkRequest,
    session: SessionDep
) -> Any:
    """
    Run a single benchmark experiment.
    
    Trains a UQ method on the specified dataset configuration and returns
    the accuracy and uncertainty estimates.
    """
    _check_uq_benchmarks_available()
    
    logger.info(f"Running single benchmark: {request.name}")
    logger.info(f"Method: {request.method.method_name}")
    logger.info(f"Dataset: {request.dataset.dataset_name}")
    
    try:
        # Get method
        method = _get_method(request.method.method_name, request.method.num_samples)
        
        # Load dataset
        dataset = _load_dataset(request.dataset)
        
        # Train and evaluate
        train_config = {
            'epochs': request.training.epochs,
            'batch_size': request.training.batch_size,
            'verbose': request.training.verbose
        }
        eval_config = {
            'batch_size': request.training.batch_size,
            'num_samples': request.method.num_samples
        }
        
        accuracy, aleatoric, epistemic = method.train_and_evaluate(
            dataset, train_config, eval_config
        )
        
        # Create experiment record
        # Get or create test user
        user = session.exec(select(User)).first()
        if not user:
            raise HTTPException(status_code=500, detail="No user found in database")
        
        experiment = UncertaintyExperiment(
            name=request.name,
            config_yaml=f"# UQ Benchmark\nmethod: {request.method.method_name}\n",
            status=JobStatus.COMPLETED,
            progress=1.0,
            aleatoric_auroc=float(aleatoric),
            epistemic_auroc=float(epistemic),
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            created_by_id=user.id
        )
        
        session.add(experiment)
        session.commit()
        session.refresh(experiment)
        
        logger.info(f"Benchmark completed: accuracy={accuracy:.3f}, aleatoric={aleatoric:.3f}, epistemic={epistemic:.3f}")
        
        return BenchmarkResponse(
            id=str(experiment.id),
            name=experiment.name,
            status=experiment.status,
            method_name=request.method.method_name,
            accuracy=float(accuracy),
            aleatoric_uncertainty=float(aleatoric),
            epistemic_uncertainty=float(epistemic),
            created_at=experiment.created_at,
            message="Benchmark completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Benchmark failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Benchmark execution failed: {str(e)}")


@router.post("/label-noise-sweep", response_model=BenchmarkResultsResponse)
async def run_label_noise_sweep(
    request: LabelNoiseSweepRequest,
    session: SessionDep
) -> Any:
    """
    Run label noise sweep benchmark.
    
    Sweeps over different noise rates to validate the C1 criterion:
    Aleatoric uncertainty should increase with label noise.
    """
    _check_uq_benchmarks_available()
    
    logger.info(f"Running label noise sweep: {request.name}")
    logger.info(f"Noise rates: {request.noise_rates}")
    
    try:
        # Get method
        method = _get_method(request.method.method_name, request.method.num_samples)
        
        # Define dataset generator
        def dataset_gen(noise_rate: float):
            config = request.dataset.copy()
            config.noise_rate = noise_rate
            return _load_dataset(config)
        
        # Run benchmark
        train_config = {
            'epochs': request.training.epochs,
            'batch_size': request.training.batch_size,
            'verbose': request.training.verbose
        }
        eval_config = {
            'batch_size': request.training.batch_size,
            'num_samples': request.method.num_samples
        }
        
        results = method.run_benchmark(
            dataset_generator=dataset_gen,
            parameter_values=request.noise_rates,
            train_config=train_config,
            eval_config=eval_config
        )
        
        logger.info(f"Sweep completed: {len(results.accuracies)} experiments")
        
        # Create a summary experiment record
        user = session.exec(select(User)).first()
        if not user:
            raise HTTPException(status_code=500, detail="No user found in database")
        
        experiment = UncertaintyExperiment(
            name=request.name,
            config_yaml=f"# Label Noise Sweep\nmethod: {request.method.method_name}\nnoise_rates: {request.noise_rates}\n",
            status=JobStatus.COMPLETED,
            progress=1.0,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            created_by_id=user.id
        )
        
        session.add(experiment)
        session.commit()
        session.refresh(experiment)
        
        return BenchmarkResultsResponse(
            id=str(experiment.id),
            name=experiment.name,
            method_name=request.method.method_name,
            parameter_name="noise_rate",
            parameter_values=results.changed_parameter_values,
            accuracies=results.accuracies,
            aleatoric_uncertainties=results.aleatoric_uncertainties,
            epistemic_uncertainties=results.epistemic_uncertainties,
            created_at=experiment.created_at
        )
        
    except Exception as e:
        logger.error(f"Label noise sweep failed: {str(e)}")


# ============================================================================
# GET Endpoints for Sweep Results
# ============================================================================

class SweepSummary(BaseModel):
    """Summary of a benchmark sweep."""
    id: str
    method_name: str
    sweep_parameter: str
    created_at: str
    num_results: int


class SweepResultDetail(BaseModel):
    """Individual result within a sweep."""
    parameter_value: float
    epistemic_uncertainty: float
    aleatoric_uncertainty: float
    accuracy: float


class SweepDetailResponse(BaseModel):
    """Detailed sweep results."""
    id: str
    method_name: str
    sweep_parameter: str
    created_at: str
    results: List[SweepResultDetail]


@router.get("/sweeps", response_model=List[SweepSummary])
async def list_sweeps(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    List all benchmark sweeps.
    
    Returns summary information for each sweep including:
    - Sweep ID
    - Method name
    - Parameter being swept
    - Creation timestamp
    - Number of results
    """
    try:
        # Query all sweeps
        statement = select(BenchmarkSweep).offset(skip).limit(limit)
        sweeps = session.exec(statement).all()
        
        # Convert to response format
        sweep_summaries = []
        for sweep in sweeps:
            # Count results for this sweep
            result_statement = select(BenchmarkResult).where(
                BenchmarkResult.sweep_id == sweep.id
            )
            num_results = len(session.exec(result_statement).all())
            
            sweep_summaries.append(SweepSummary(
                id=str(sweep.id),
                method_name=sweep.method,
                sweep_parameter=sweep.sweep_parameter,
                created_at=sweep.created_at.isoformat() if sweep.created_at else "",
                num_results=num_results
            ))
        
        return sweep_summaries
        
    except Exception as e:
        logger.error(f"Failed to list sweeps: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list sweeps: {str(e)}")


@router.get("/sweeps/{sweep_id}", response_model=SweepDetailResponse)
async def get_sweep_details(
    sweep_id: str,
    session: SessionDep
) -> Any:
    """
    Get detailed results for a specific sweep.
    
    Returns:
    - Sweep metadata
    - All results with parameter values, uncertainties, and accuracy
    """
    try:
        # Get sweep
        sweep = session.get(BenchmarkSweep, sweep_id)
        if not sweep:
            raise HTTPException(status_code=404, detail=f"Sweep {sweep_id} not found")
        
        # Get all results for this sweep
        statement = select(BenchmarkResult).where(
            BenchmarkResult.sweep_id == sweep_id
        )
        
        results = session.exec(statement).all()
        
        # Sort by parameter value
        sorted_results = sorted(results, key=lambda r: r.parameter_value or 0.0)
        
        # Convert to response format
        result_details = [
            SweepResultDetail(
                parameter_value=result.parameter_value or 0.0,
                epistemic_uncertainty=result.epistemic_uncertainty,
                aleatoric_uncertainty=result.aleatoric_uncertainty,
                accuracy=result.accuracy
            )
            for result in sorted_results
        ]
        
        return SweepDetailResponse(
            id=str(sweep.id),
            method_name=sweep.method,
            sweep_parameter=sweep.sweep_parameter,
            created_at=sweep.created_at.isoformat() if sweep.created_at else "",
            results=result_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sweep details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sweep details: {str(e)}")


# ============================================================================
# Simplified request models for UI
# ============================================================================

class SimpleSweepRequest(BaseModel):
    """Simplified sweep request from UI."""
    method_name: str
    sweep_parameter: str
    sweep_values: List[float]
    base_config: dict


# ============================================================================
# Alias endpoints to match UI expectations
# ============================================================================

@router.post("/run", response_model=BenchmarkResponse)
async def run_benchmark_alias(
    request: SingleBenchmarkRequest,
    session: SessionDep
) -> Any:
    """Alias for /single endpoint to match UI expectations."""
    return await run_single_benchmark(request, session)


@router.post("/sweep")
async def run_sweep_alias(
    request: SimpleSweepRequest,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Simplified sweep endpoint that matches UI expectations.
    Transforms simple request into full LabelNoiseSweepRequest format.
    """
    try:
        # Transform simple request into full format
        full_request = LabelNoiseSweepRequest(
            name=f"sweep_{request.method_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=f"Parameter sweep: {request.sweep_parameter}",
            method=BenchmarkMethodConfig(
                method_name=request.method_name,
                num_samples=20
            ),
            dataset=BenchmarkDatasetConfig(
                dataset_name="cifar10",
                test_mode=False,
                under_supported_classes=[3, 5],
                under_train_per_class=50,
                regular_train_per_class=300,
                eval_per_class=request.base_config.get("test_samples", 1000) // 10,
                noise_rate=0.0,  # Will be swept
                seed=42
            ),
            training=BenchmarkTrainingConfig(
                epochs=request.base_config.get("epochs", 10),
                batch_size=256,
                learning_rate=0.001
            ),
            noise_rates=request.sweep_values
        )
        
        # Call the full endpoint
        return await run_label_noise_sweep(full_request, session)
        
    except Exception as e:
        logger.error(f"Sweep failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sweep failed: {str(e)}")

# Made with Bob
