# Modular Storage Architecture for UQ Benchmarks

## Overview

This document describes the modular storage architecture implemented for the UQ benchmarks system. The architecture follows the **Service Layer Pattern** and enables seamless switching between different storage backends (PostgreSQL, watsonx.governance, etc.).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Routes                          │
│              (app/api/routes/uq_benchmarks.py)              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   MetricsService                            │
│              (app/services/metrics_service.py)              │
│                                                             │
│  • Orchestrates multiple storage backends                  │
│  • Error isolation (failures don't cascade)                │
│  • Unified interface for API layer                         │
└────────────┬────────────────────────────┬───────────────────┘
             │                            │
             ▼                            ▼
┌────────────────────────┐   ┌──────────────────────────────┐
│   PostgresStorage      │   │      WxGovStorage            │
│  (storage/postgres.py) │   │    (storage/wxgov.py)        │
│                        │   │                              │
│  • SQLModel/PostgreSQL │   │  • ibm_aigov_facts_client   │
│  • Direct DB access    │   │  • Governance tracking      │
│  • Fast queries        │   │  • Compliance monitoring    │
└────────────────────────┘   └──────────────────────────────┘
```

## Key Components

### 1. Storage Interface (`app/services/storage/base.py`)

Abstract base class defining the contract for all storage backends:

```python
class MetricsStorage(ABC):
    @abstractmethod
    async def save_result(self, result: BenchmarkResult) -> BenchmarkResult
    
    @abstractmethod
    async def get_result(self, result_id: uuid.UUID) -> Optional[BenchmarkResult]
    
    @abstractmethod
    async def list_results(self, skip: int, limit: int, sweep_id: Optional[uuid.UUID]) -> List[BenchmarkResult]
    
    @abstractmethod
    async def save_sweep(self, sweep: BenchmarkSweep) -> BenchmarkSweep
    
    @abstractmethod
    async def get_sweep(self, sweep_id: uuid.UUID) -> Optional[BenchmarkSweep]
    
    @abstractmethod
    async def list_sweeps(self, skip: int, limit: int) -> List[BenchmarkSweep]
```

### 2. PostgreSQL Implementation (`app/services/storage/postgres.py`)

Stores metrics in PostgreSQL using SQLModel:

- **Pros**: Fast queries, ACID compliance, full SQL capabilities
- **Use case**: Primary storage for application data
- **Configuration**: Enabled by default via `ENABLE_POSTGRES=True`

### 3. watsonx.governance Implementation (`app/services/storage/wxgov.py`)

Stores metrics in watsonx.governance for AI governance:

- **Pros**: Governance tracking, compliance monitoring, model lifecycle management
- **Use case**: Enterprise AI governance and compliance
- **Configuration**: Optional, requires `ENABLE_WXGOV=True` and API credentials

**Schema Transformation**: The `_transform_to_wxgov()` method adapts `BenchmarkResult` to wx.gov schema:

```python
{
    "model_id": "uq_benchmark_gaussian_logits_...",
    "metrics": {
        "test_accuracy": 0.85,
        "aleatoric_uncertainty": 0.12,
        "epistemic_uncertainty": 0.08
    },
    "governance_metadata": {
        "risk_level": "medium",
        "use_case": "uncertainty_quantification",
        "data_classification": "research"
    }
}
```

### 4. Metrics Service (`app/services/metrics_service.py`)

Orchestrates multiple storage backends:

- **Multi-backend writes**: Saves to all configured storages
- **Error isolation**: Failure in one backend doesn't affect others
- **Flexible reads**: Query specific storage by index
- **Comprehensive logging**: Track all operations

### 5. Dependency Injection (`app/api/deps.py`)

Factory function that instantiates storage backends based on configuration:

```python
def get_metrics_service(session: SessionDep) -> MetricsService:
    storages = []
    
    if settings.ENABLE_POSTGRES:
        storages.append(PostgresStorage(session))
    
    if settings.ENABLE_WXGOV and all([settings.WXGOV_API_KEY, ...]):
        storages.append(WxGovStorage(...))
    
    return MetricsService(storages)
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Storage Backend Configuration
ENABLE_POSTGRES=true          # Enable PostgreSQL storage (default: true)
ENABLE_WXGOV=false           # Enable watsonx.governance storage (default: false)

# watsonx.governance Configuration (optional)
WXGOV_API_KEY=your_api_key
WXGOV_SPACE_ID=your_space_id
WXGOV_URL=https://api.dataplatform.cloud.ibm.com
```

### Configuration Class (`app/core/config.py`)

```python
class Settings(BaseSettings):
    # Storage backend configuration
    ENABLE_POSTGRES: bool = True
    ENABLE_WXGOV: bool = False
    
    # watsonx.governance configuration (optional)
    WXGOV_API_KEY: str | None = None
    WXGOV_SPACE_ID: str | None = None
    WXGOV_URL: str | None = None
```

## Database Schema Updates

### New Fields in `BenchmarkResult` (`app/tables.py`)

Added wx.gov compatibility fields (all optional for backward compatibility):

```python
class BenchmarkResult(SQLModel, table=True):
    # ... existing fields ...
    
    # wx.gov compatibility fields
    training_loss: float | None = None
    risk_level: str | None = Field(default=None, max_length=50)
    use_case: str = Field(default="uncertainty_quantification", max_length=100)
    data_classification: str = Field(default="research", max_length=50)
    wx_gov_model_id: str | None = Field(default=None, max_length=255)
    wx_gov_run_id: str | None = Field(default=None, max_length=255)
```

## Usage Examples

### Example 1: Using MetricsService in API Routes

```python
from app.api.deps import MetricsServiceDep
from app.tables import BenchmarkResult

@router.post("/benchmark")
async def run_benchmark(
    request: BenchmarkRequest,
    metrics_service: MetricsServiceDep
):
    # Create result
    result = BenchmarkResult(
        method="gaussian_logits",
        framework="keras",
        accuracy=0.85,
        aleatoric_uncertainty=0.12,
        epistemic_uncertainty=0.08,
        # ... other fields ...
    )
    
    # Save to all configured storages
    saved_result = await metrics_service.save_result(result)
    
    return saved_result
```

### Example 2: Querying Results

```python
# Get result from primary storage (PostgreSQL)
result = await metrics_service.get_result(result_id, storage_index=0)

# List results with pagination
results = await metrics_service.list_results(skip=0, limit=10)

# List results for a specific sweep
sweep_results = await metrics_service.list_results(
    skip=0, 
    limit=100, 
    sweep_id=sweep_id
)
```

### Example 3: Configuration Scenarios

**Scenario 1: PostgreSQL Only (Default)**
```bash
ENABLE_POSTGRES=true
ENABLE_WXGOV=false
```
- Fast, local storage
- No external dependencies
- Ideal for development

**Scenario 2: PostgreSQL + watsonx.governance**
```bash
ENABLE_POSTGRES=true
ENABLE_WXGOV=true
WXGOV_API_KEY=your_key
WXGOV_SPACE_ID=your_space
WXGOV_URL=https://api.dataplatform.cloud.ibm.com
```
- Dual storage for redundancy
- Governance tracking enabled
- Ideal for production with compliance requirements

**Scenario 3: watsonx.governance Only**
```bash
ENABLE_POSTGRES=false
ENABLE_WXGOV=true
WXGOV_API_KEY=your_key
WXGOV_SPACE_ID=your_space
WXGOV_URL=https://api.dataplatform.cloud.ibm.com
```
- Cloud-native governance
- No local database required
- Ideal for serverless deployments

## Error Handling

The `MetricsService` implements robust error handling:

1. **Partial Failures**: If one storage fails, others continue
2. **Logging**: All failures are logged with context
3. **Complete Failures**: Only fails if ALL storages fail

```python
async def save_result(self, result: BenchmarkResult) -> BenchmarkResult:
    errors = []
    
    for storage in self.storages:
        try:
            saved_result = await storage.save_result(result)
        except Exception as e:
            logger.error(f"Failed to save to {storage.__class__.__name__}: {e}")
            errors.append(str(e))
    
    if errors and len(errors) == len(self.storages):
        raise Exception(f"Failed to save to all storages: {'; '.join(errors)}")
    
    return saved_result
```

## Migration Guide

### Adding a New Storage Backend

1. **Create implementation** in `app/services/storage/your_storage.py`:
```python
from app.services.storage.base import MetricsStorage

class YourStorage(MetricsStorage):
    async def save_result(self, result: BenchmarkResult) -> BenchmarkResult:
        # Your implementation
        pass
    # ... implement other methods
```

2. **Update configuration** in `app/core/config.py`:
```python
ENABLE_YOUR_STORAGE: bool = False
YOUR_STORAGE_CONFIG: str | None = None
```

3. **Update dependency injection** in `app/api/deps.py`:
```python
if settings.ENABLE_YOUR_STORAGE:
    storages.append(YourStorage(settings.YOUR_STORAGE_CONFIG))
```

4. **Export from package** in `app/services/storage/__init__.py`:
```python
from app.services.storage.your_storage import YourStorage
__all__ = [..., "YourStorage"]
```

## Testing

### Unit Tests

Test each storage backend independently:

```python
import pytest
from app.services.storage.postgres import PostgresStorage

@pytest.mark.asyncio
async def test_postgres_save_result(db_session):
    storage = PostgresStorage(db_session)
    result = BenchmarkResult(...)
    
    saved = await storage.save_result(result)
    assert saved.id is not None
```

### Integration Tests

Test the full service with multiple backends:

```python
@pytest.mark.asyncio
async def test_metrics_service_multi_backend(db_session):
    postgres = PostgresStorage(db_session)
    service = MetricsService([postgres])
    
    result = BenchmarkResult(...)
    saved = await service.save_result(result)
    
    retrieved = await service.get_result(saved.id)
    assert retrieved.id == saved.id
```

## Performance Considerations

1. **Write Performance**: Writes to multiple backends are sequential (not parallel)
   - Future optimization: Use `asyncio.gather()` for parallel writes
   
2. **Read Performance**: Reads from single backend (fast)
   - Default: PostgreSQL (storage_index=0)
   
3. **Network Latency**: wx.gov calls involve network overhead
   - Consider caching for frequently accessed data

## Security

1. **API Keys**: Store wx.gov credentials in environment variables, never in code
2. **Database Access**: Use connection pooling and prepared statements
3. **Data Classification**: Set appropriate `data_classification` field values
4. **Risk Levels**: Configure `risk_level` based on model sensitivity

## Future Enhancements

1. **Parallel Writes**: Use `asyncio.gather()` for concurrent storage writes
2. **Caching Layer**: Add Redis for frequently accessed metrics
3. **Event Streaming**: Publish metrics to Kafka/RabbitMQ
4. **Storage Fallback**: Automatic failover if primary storage unavailable
5. **Metrics Aggregation**: Pre-compute statistics across sweeps
6. **Storage Health Checks**: Monitor backend availability

## Troubleshooting

### Issue: wx.gov storage fails silently

**Solution**: Check logs for error messages. Verify credentials:
```bash
# Check if credentials are set
echo $WXGOV_API_KEY
echo $WXGOV_SPACE_ID
```

### Issue: PostgreSQL connection errors

**Solution**: Verify database configuration:
```python
# In app/core/config.py
POSTGRES_SERVER = "localhost"
POSTGRES_PORT = 5432
POSTGRES_USER = "your_user"
POSTGRES_PASSWORD = "your_password"
POSTGRES_DB = "your_db"
```

### Issue: Import errors for storage modules

**Solution**: Ensure all `__init__.py` files are present:
- `app/services/__init__.py`
- `app/services/storage/__init__.py`

## References

- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)
- [Dependency Injection in FastAPI](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [watsonx.governance Documentation](https://www.ibm.com/docs/en/watsonx/saas)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)

---

**Implementation Date**: 2026-05-24  
**Version**: 1.0.0  
**Status**: Production Ready