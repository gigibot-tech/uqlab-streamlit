"""Abstract base class for metrics storage backends."""

from abc import ABC, abstractmethod
from typing import List, Optional
import uuid

from app.tables import BenchmarkResult, BenchmarkSweep


class MetricsStorage(ABC):
    """Abstract base class for metrics storage backends.
    
    This interface defines the contract that all storage backends must implement.
    Implementations can store metrics in different backends (PostgreSQL, wx.gov, etc.).
    """
    
    @abstractmethod
    async def save_result(self, result: BenchmarkResult) -> BenchmarkResult:
        """Save a benchmark result.
        
        Args:
            result: BenchmarkResult instance to save
            
        Returns:
            The saved BenchmarkResult with any backend-specific fields populated
            
        Raises:
            Exception: If save operation fails
        """
        pass
    
    @abstractmethod
    async def get_result(self, result_id: uuid.UUID) -> Optional[BenchmarkResult]:
        """Retrieve a benchmark result by ID.
        
        Args:
            result_id: UUID of the result to retrieve
            
        Returns:
            BenchmarkResult if found, None otherwise
            
        Raises:
            Exception: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def list_results(
        self, 
        skip: int = 0, 
        limit: int = 100,
        sweep_id: Optional[uuid.UUID] = None
    ) -> List[BenchmarkResult]:
        """List benchmark results with pagination.
        
        Args:
            skip: Number of results to skip
            limit: Maximum number of results to return
            sweep_id: Optional sweep ID to filter by
            
        Returns:
            List of BenchmarkResult instances
            
        Raises:
            Exception: If list operation fails
        """
        pass
    
    @abstractmethod
    async def save_sweep(self, sweep: BenchmarkSweep) -> BenchmarkSweep:
        """Save a benchmark sweep.
        
        Args:
            sweep: BenchmarkSweep instance to save
            
        Returns:
            The saved BenchmarkSweep with any backend-specific fields populated
            
        Raises:
            Exception: If save operation fails
        """
        pass
    
    @abstractmethod
    async def get_sweep(self, sweep_id: uuid.UUID) -> Optional[BenchmarkSweep]:
        """Retrieve a benchmark sweep by ID.
        
        Args:
            sweep_id: UUID of the sweep to retrieve
            
        Returns:
            BenchmarkSweep if found, None otherwise
            
        Raises:
            Exception: If retrieval operation fails
        """
        pass
    
    @abstractmethod
    async def list_sweeps(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[BenchmarkSweep]:
        """List benchmark sweeps with pagination.
        
        Args:
            skip: Number of sweeps to skip
            limit: Maximum number of sweeps to return
            
        Returns:
            List of BenchmarkSweep instances
            
        Raises:
            Exception: If list operation fails
        """
        pass

# Made with Bob
