"""watsonx.governance storage backend for metrics."""

import logging
from typing import List, Optional, Dict, Any
import uuid
import json
from datetime import datetime

from app.services.storage.base import MetricsStorage
from app.tables import BenchmarkResult, BenchmarkSweep

logger = logging.getLogger(__name__)


class WxGovStorage(MetricsStorage):
    """watsonx.governance implementation of MetricsStorage.
    
    Stores benchmark results in watsonx.governance using the ibm_aigov_facts_client SDK.
    This enables governance tracking, compliance monitoring, and model lifecycle management.
    """
    
    def __init__(self, api_key: str, space_id: str, url: str):
        """Initialize wx.gov storage.
        
        Args:
            api_key: IBM Cloud API key for authentication
            space_id: watsonx.governance space ID
            url: watsonx.governance API URL
        """
        self.api_key = api_key
        self.space_id = space_id
        self.url = url
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of wx.gov client."""
        if self._client is None:
            try:
                from ibm_aigov_facts_client import AIGovFactsClient
                self._client = AIGovFactsClient(
                    api_key=self.api_key,
                    space_id=self.space_id,
                    service_url=self.url
                )
                logger.info("Initialized watsonx.governance client")
            except ImportError:
                logger.error("ibm_aigov_facts_client not installed. Install with: pip install ibm-aigov-facts-client")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize wx.gov client: {str(e)}")
                raise
        return self._client
    
    def _transform_to_wxgov(self, result: BenchmarkResult) -> Dict[str, Any]:
        """Transform BenchmarkResult to wx.gov schema.
        
        Args:
            result: BenchmarkResult instance
            
        Returns:
            Dictionary with wx.gov compatible schema
        """
        # Parse configuration JSONs
        dataset_config = json.loads(result.dataset_config_json) if result.dataset_config_json else {}
        training_config = json.loads(result.training_config_json) if result.training_config_json else {}
        
        # Build wx.gov fact record
        wxgov_record = {
            "model_id": result.wx_gov_model_id or f"uq_benchmark_{result.method}_{result.id}",
            "model_name": f"{result.method}_{result.framework}",
            "model_type": "uncertainty_quantification",
            "framework": result.framework,
            
            # Metrics (wx.gov requires specific metric names)
            "metrics": {
                "test_accuracy": float(result.accuracy),
                "aleatoric_uncertainty": float(result.aleatoric_uncertainty),
                "epistemic_uncertainty": float(result.epistemic_uncertainty),
                "training_loss": float(result.training_loss) if result.training_loss else None,
                "training_time_seconds": float(result.training_time),
                "evaluation_time_seconds": float(result.evaluation_time),
            },
            
            # Governance metadata
            "governance_metadata": {
                "risk_level": result.risk_level or "medium",
                "use_case": result.use_case,
                "data_classification": result.data_classification,
                "compliance_tags": ["research", "uncertainty_quantification"],
            },
            
            # Training configuration
            "training_config": training_config,
            
            # Dataset information
            "dataset_info": {
                "name": dataset_config.get("dataset_name", "unknown"),
                "noise_rate": dataset_config.get("noise_rate", 0.0),
                "train_samples": dataset_config.get("regular_train_per_class", 0) * 10,  # Approximate
            },
            
            # Timestamps
            "created_at": result.created_at.isoformat() if result.created_at else datetime.utcnow().isoformat(),
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            
            # Additional metadata
            "metadata": {
                "benchmark_id": str(result.id),
                "sweep_id": str(result.sweep_id) if result.sweep_id else None,
                "parameter_value": result.parameter_value,
                "status": result.status,
            }
        }
        
        return wxgov_record
    
    async def save_result(self, result: BenchmarkResult) -> BenchmarkResult:
        """Save a benchmark result to wx.gov.
        
        Args:
            result: BenchmarkResult instance to save
            
        Returns:
            The BenchmarkResult with wx_gov_run_id populated
            
        Raises:
            Exception: If wx.gov operation fails
        """
        try:
            client = self._get_client()
            wxgov_record = self._transform_to_wxgov(result)
            
            # Store fact in wx.gov
            response = client.store_model_facts(wxgov_record)
            
            # Update result with wx.gov IDs
            if response and "run_id" in response:
                result.wx_gov_run_id = response["run_id"]
            if "model_id" in wxgov_record:
                result.wx_gov_model_id = wxgov_record["model_id"]
            
            logger.info(f"Saved benchmark result {result.id} to watsonx.governance (run_id: {result.wx_gov_run_id})")
            return result
            
        except Exception as e:
            logger.error(f"Failed to save result to wx.gov: {str(e)}")
            raise
    
    async def get_result(self, result_id: uuid.UUID) -> Optional[BenchmarkResult]:
        """Retrieve a benchmark result from wx.gov.
        
        Note: This is a placeholder. wx.gov doesn't support direct retrieval by our internal ID.
        In practice, you would query by wx_gov_run_id or model_id.
        
        Args:
            result_id: UUID of the result to retrieve
            
        Returns:
            None (not supported by wx.gov directly)
        """
        logger.warning("Direct retrieval by internal ID not supported by wx.gov")
        return None
    
    async def list_results(
        self, 
        skip: int = 0, 
        limit: int = 100,
        sweep_id: Optional[uuid.UUID] = None
    ) -> List[BenchmarkResult]:
        """List benchmark results from wx.gov.
        
        Note: This queries wx.gov for model facts and converts them back to BenchmarkResult.
        
        Args:
            skip: Number of results to skip
            limit: Maximum number of results to return
            sweep_id: Optional sweep ID to filter by
            
        Returns:
            List of BenchmarkResult instances
        """
        try:
            client = self._get_client()
            
            # Query wx.gov for model facts
            query_params = {
                "model_type": "uncertainty_quantification",
                "limit": limit,
                "offset": skip
            }
            
            if sweep_id:
                query_params["metadata.sweep_id"] = str(sweep_id)
            
            response = client.query_model_facts(query_params)
            
            # Convert wx.gov records back to BenchmarkResult
            results = []
            for record in response.get("results", []):
                # This is a simplified conversion - in practice you'd need full reconstruction
                logger.debug(f"Retrieved wx.gov record: {record.get('model_id')}")
                # Note: Full reconstruction would require additional logic
            
            logger.debug(f"Listed {len(results)} benchmark results from wx.gov")
            return results
            
        except Exception as e:
            logger.error(f"Failed to list results from wx.gov: {str(e)}")
            raise
    
    async def save_sweep(self, sweep: BenchmarkSweep) -> BenchmarkSweep:
        """Save a benchmark sweep to wx.gov.
        
        Sweeps are stored as model experiment groups in wx.gov.
        
        Args:
            sweep: BenchmarkSweep instance to save
            
        Returns:
            The BenchmarkSweep (wx.gov doesn't provide additional IDs for sweeps)
        """
        try:
            client = self._get_client()
            
            # Create experiment group in wx.gov
            sweep_record = {
                "experiment_id": str(sweep.id),
                "experiment_name": sweep.name,
                "experiment_type": "parameter_sweep",
                "method": sweep.method,
                "sweep_parameter": sweep.sweep_parameter,
                "sweep_values": json.loads(sweep.sweep_values_json),
                "base_config": json.loads(sweep.base_config_json),
                "created_at": sweep.created_at.isoformat() if sweep.created_at else datetime.utcnow().isoformat(),
            }
            
            # Store experiment metadata
            client.store_experiment_metadata(sweep_record)
            
            logger.info(f"Saved benchmark sweep {sweep.id} to watsonx.governance")
            return sweep
            
        except Exception as e:
            logger.error(f"Failed to save sweep to wx.gov: {str(e)}")
            raise
    
    async def get_sweep(self, sweep_id: uuid.UUID) -> Optional[BenchmarkSweep]:
        """Retrieve a benchmark sweep from wx.gov.
        
        Note: Limited support - wx.gov doesn't have direct sweep retrieval.
        
        Args:
            sweep_id: UUID of the sweep to retrieve
            
        Returns:
            None (not fully supported by wx.gov)
        """
        logger.warning("Direct sweep retrieval not fully supported by wx.gov")
        return None
    
    async def list_sweeps(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[BenchmarkSweep]:
        """List benchmark sweeps from wx.gov.
        
        Args:
            skip: Number of sweeps to skip
            limit: Maximum number of sweeps to return
            
        Returns:
            List of BenchmarkSweep instances
        """
        try:
            client = self._get_client()
            
            # Query wx.gov for experiment metadata
            query_params = {
                "experiment_type": "parameter_sweep",
                "limit": limit,
                "offset": skip
            }
            
            response = client.query_experiment_metadata(query_params)
            
            # Convert to BenchmarkSweep instances
            sweeps = []
            for record in response.get("results", []):
                logger.debug(f"Retrieved wx.gov experiment: {record.get('experiment_id')}")
                # Note: Full reconstruction would require additional logic
            
            logger.debug(f"Listed {len(sweeps)} benchmark sweeps from wx.gov")
            return sweeps
            
        except Exception as e:
            logger.error(f"Failed to list sweeps from wx.gov: {str(e)}")
            raise

# Made with Bob
