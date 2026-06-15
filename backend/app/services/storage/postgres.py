"""PostgreSQL storage backend for metrics."""

import logging
from typing import List, Optional
import uuid

from sqlmodel import Session, select

from app.services.storage.base import MetricsStorage
from app.tables import BenchmarkResult, BenchmarkSweep

logger = logging.getLogger(__name__)


class PostgresStorage(MetricsStorage):
    """PostgreSQL implementation of MetricsStorage.
    
    Stores benchmark results and sweeps in PostgreSQL database using SQLModel.
    """
    
    def __init__(self, session: Session):
        """Initialize PostgreSQL storage.
        
        Args:
            session: SQLModel database session
        """
        self.session = session
    
    async def save_result(self, result: BenchmarkResult) -> BenchmarkResult:
        """Save a benchmark result to PostgreSQL.
        
        Args:
            result: BenchmarkResult instance to save
            
        Returns:
            The saved BenchmarkResult with ID populated
            
        Raises:
            Exception: If database operation fails
        """
        try:
            self.session.add(result)
            self.session.commit()
            self.session.refresh(result)
            logger.info(f"Saved benchmark result {result.id} to PostgreSQL")
            return result
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to save result to PostgreSQL: {str(e)}")
            raise
    
    async def get_result(self, result_id: uuid.UUID) -> Optional[BenchmarkResult]:
        """Retrieve a benchmark result from PostgreSQL.
        
        Args:
            result_id: UUID of the result to retrieve
            
        Returns:
            BenchmarkResult if found, None otherwise
        """
        try:
            result = self.session.get(BenchmarkResult, result_id)
            if result:
                logger.debug(f"Retrieved benchmark result {result_id} from PostgreSQL")
            return result
        except Exception as e:
            logger.error(f"Failed to get result from PostgreSQL: {str(e)}")
            raise
    
    async def list_results(
        self, 
        skip: int = 0, 
        limit: int = 100,
        sweep_id: Optional[uuid.UUID] = None
    ) -> List[BenchmarkResult]:
        """List benchmark results from PostgreSQL.
        
        Args:
            skip: Number of results to skip
            limit: Maximum number of results to return
            sweep_id: Optional sweep ID to filter by
            
        Returns:
            List of BenchmarkResult instances
        """
        try:
            statement = select(BenchmarkResult)
            
            if sweep_id:
                statement = statement.where(BenchmarkResult.sweep_id == sweep_id)
            
            statement = statement.offset(skip).limit(limit)
            results = self.session.exec(statement).all()
            
            logger.debug(f"Listed {len(results)} benchmark results from PostgreSQL")
            return list(results)
        except Exception as e:
            logger.error(f"Failed to list results from PostgreSQL: {str(e)}")
            raise
    
    async def save_sweep(self, sweep: BenchmarkSweep) -> BenchmarkSweep:
        """Save a benchmark sweep to PostgreSQL.
        
        Args:
            sweep: BenchmarkSweep instance to save
            
        Returns:
            The saved BenchmarkSweep with ID populated
            
        Raises:
            Exception: If database operation fails
        """
        try:
            self.session.add(sweep)
            self.session.commit()
            self.session.refresh(sweep)
            logger.info(f"Saved benchmark sweep {sweep.id} to PostgreSQL")
            return sweep
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to save sweep to PostgreSQL: {str(e)}")
            raise
    
    async def get_sweep(self, sweep_id: uuid.UUID) -> Optional[BenchmarkSweep]:
        """Retrieve a benchmark sweep from PostgreSQL.
        
        Args:
            sweep_id: UUID of the sweep to retrieve
            
        Returns:
            BenchmarkSweep if found, None otherwise
        """
        try:
            sweep = self.session.get(BenchmarkSweep, sweep_id)
            if sweep:
                logger.debug(f"Retrieved benchmark sweep {sweep_id} from PostgreSQL")
            return sweep
        except Exception as e:
            logger.error(f"Failed to get sweep from PostgreSQL: {str(e)}")
            raise
    
    async def list_sweeps(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[BenchmarkSweep]:
        """List benchmark sweeps from PostgreSQL.
        
        Args:
            skip: Number of sweeps to skip
            limit: Maximum number of sweeps to return
            
        Returns:
            List of BenchmarkSweep instances
        """
        try:
            statement = select(BenchmarkSweep).offset(skip).limit(limit)
            sweeps = self.session.exec(statement).all()
            
            logger.debug(f"Listed {len(sweeps)} benchmark sweeps from PostgreSQL")
            return list(sweeps)
        except Exception as e:
            logger.error(f"Failed to list sweeps from PostgreSQL: {str(e)}")
            raise

# Made with Bob
