"""Metrics service for orchestrating multiple storage backends."""

import logging
from typing import List, Optional
import uuid

from app.services.storage.base import MetricsStorage
from app.tables import BenchmarkResult, BenchmarkSweep

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for managing benchmark metrics across multiple storage backends.
    
    This service implements the service layer pattern, coordinating writes to
    multiple storage backends (PostgreSQL, wx.gov, etc.) while providing a
    unified interface for the API layer.
    
    Key features:
    - Multi-backend support: Save to multiple storages simultaneously
    - Error isolation: Failures in one backend don't affect others
    - Flexible retrieval: Get data from specific storage backend
    - Logging: Track all operations for debugging and monitoring
    """
    
    def __init__(self, storages: List[MetricsStorage]):
        """Initialize metrics service with storage backends.
        
        Args:
            storages: List of storage backend instances
        """
        self.storages = storages
        logger.info(f"Initialized MetricsService with {len(storages)} storage backend(s)")
    
    async def save_result(self, result: BenchmarkResult) -> BenchmarkResult:
        """Save a benchmark result to all configured storage backends.
        
        Attempts to save to all backends. If one fails, logs the error but
        continues with others. Returns the result with any backend-specific
        fields populated.
        
        Args:
            result: BenchmarkResult instance to save
            
        Returns:
            The saved BenchmarkResult with backend-specific fields populated
        """
        saved_result = result
        errors = []
        
        for storage in self.storages:
            try:
                storage_name = storage.__class__.__name__
                logger.info(f"Saving result {result.id} to {storage_name}")
                saved_result = await storage.save_result(saved_result)
                logger.info(f"Successfully saved result {result.id} to {storage_name}")
            except Exception as e:
                storage_name = storage.__class__.__name__
                error_msg = f"Failed to save result to {storage_name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        if errors and len(errors) == len(self.storages):
            # All storages failed
            raise Exception(f"Failed to save result to all storages: {'; '.join(errors)}")
        
        return saved_result
    
    async def get_result(
        self, 
        result_id: uuid.UUID, 
        storage_index: int = 0
    ) -> Optional[BenchmarkResult]:
        """Retrieve a benchmark result from a specific storage backend.
        
        Args:
            result_id: UUID of the result to retrieve
            storage_index: Index of storage backend to query (default: 0 = first backend)
            
        Returns:
            BenchmarkResult if found, None otherwise
            
        Raises:
            IndexError: If storage_index is out of range
            Exception: If retrieval operation fails
        """
        if storage_index >= len(self.storages):
            raise IndexError(f"Storage index {storage_index} out of range (have {len(self.storages)} storages)")
        
        storage = self.storages[storage_index]
        storage_name = storage.__class__.__name__
        
        try:
            logger.debug(f"Retrieving result {result_id} from {storage_name}")
            result = await storage.get_result(result_id)
            if result:
                logger.debug(f"Found result {result_id} in {storage_name}")
            else:
                logger.debug(f"Result {result_id} not found in {storage_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to get result from {storage_name}: {str(e)}")
            raise
    
    async def list_results(
        self, 
        skip: int = 0, 
        limit: int = 100,
        sweep_id: Optional[uuid.UUID] = None,
        storage_index: int = 0
    ) -> List[BenchmarkResult]:
        """List benchmark results from a specific storage backend.
        
        Args:
            skip: Number of results to skip
            limit: Maximum number of results to return
            sweep_id: Optional sweep ID to filter by
            storage_index: Index of storage backend to query (default: 0 = first backend)
            
        Returns:
            List of BenchmarkResult instances
            
        Raises:
            IndexError: If storage_index is out of range
            Exception: If list operation fails
        """
        if storage_index >= len(self.storages):
            raise IndexError(f"Storage index {storage_index} out of range (have {len(self.storages)} storages)")
        
        storage = self.storages[storage_index]
        storage_name = storage.__class__.__name__
        
        try:
            logger.debug(f"Listing results from {storage_name} (skip={skip}, limit={limit})")
            results = await storage.list_results(skip, limit, sweep_id)
            logger.debug(f"Found {len(results)} results in {storage_name}")
            return results
        except Exception as e:
            logger.error(f"Failed to list results from {storage_name}: {str(e)}")
            raise
    
    async def save_sweep(self, sweep: BenchmarkSweep) -> BenchmarkSweep:
        """Save a benchmark sweep to all configured storage backends.
        
        Attempts to save to all backends. If one fails, logs the error but
        continues with others.
        
        Args:
            sweep: BenchmarkSweep instance to save
            
        Returns:
            The saved BenchmarkSweep
        """
        saved_sweep = sweep
        errors = []
        
        for storage in self.storages:
            try:
                storage_name = storage.__class__.__name__
                logger.info(f"Saving sweep {sweep.id} to {storage_name}")
                saved_sweep = await storage.save_sweep(saved_sweep)
                logger.info(f"Successfully saved sweep {sweep.id} to {storage_name}")
            except Exception as e:
                storage_name = storage.__class__.__name__
                error_msg = f"Failed to save sweep to {storage_name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        if errors and len(errors) == len(self.storages):
            # All storages failed
            raise Exception(f"Failed to save sweep to all storages: {'; '.join(errors)}")
        
        return saved_sweep
    
    async def get_sweep(
        self, 
        sweep_id: uuid.UUID, 
        storage_index: int = 0
    ) -> Optional[BenchmarkSweep]:
        """Retrieve a benchmark sweep from a specific storage backend.
        
        Args:
            sweep_id: UUID of the sweep to retrieve
            storage_index: Index of storage backend to query (default: 0 = first backend)
            
        Returns:
            BenchmarkSweep if found, None otherwise
            
        Raises:
            IndexError: If storage_index is out of range
            Exception: If retrieval operation fails
        """
        if storage_index >= len(self.storages):
            raise IndexError(f"Storage index {storage_index} out of range (have {len(self.storages)} storages)")
        
        storage = self.storages[storage_index]
        storage_name = storage.__class__.__name__
        
        try:
            logger.debug(f"Retrieving sweep {sweep_id} from {storage_name}")
            sweep = await storage.get_sweep(sweep_id)
            if sweep:
                logger.debug(f"Found sweep {sweep_id} in {storage_name}")
            else:
                logger.debug(f"Sweep {sweep_id} not found in {storage_name}")
            return sweep
        except Exception as e:
            logger.error(f"Failed to get sweep from {storage_name}: {str(e)}")
            raise
    
    async def list_sweeps(
        self, 
        skip: int = 0, 
        limit: int = 100,
        storage_index: int = 0
    ) -> List[BenchmarkSweep]:
        """List benchmark sweeps from a specific storage backend.
        
        Args:
            skip: Number of sweeps to skip
            limit: Maximum number of sweeps to return
            storage_index: Index of storage backend to query (default: 0 = first backend)
            
        Returns:
            List of BenchmarkSweep instances
            
        Raises:
            IndexError: If storage_index is out of range
            Exception: If list operation fails
        """
        if storage_index >= len(self.storages):
            raise IndexError(f"Storage index {storage_index} out of range (have {len(self.storages)} storages)")
        
        storage = self.storages[storage_index]
        storage_name = storage.__class__.__name__
        
        try:
            logger.debug(f"Listing sweeps from {storage_name} (skip={skip}, limit={limit})")
            sweeps = await storage.list_sweeps(skip, limit)
            logger.debug(f"Found {len(sweeps)} sweeps in {storage_name}")
            return sweeps
        except Exception as e:
            logger.error(f"Failed to list sweeps from {storage_name}: {str(e)}")
            raise

# Made with Bob
