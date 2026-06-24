# Architecture Decision: Task Execution Strategy

## Decision: Use Subprocess Executor (for now)

### Context
Need to execute long-running ML training tasks from FastAPI backend.

### Options Considered

#### 1. Subprocess (asyncio.create_subprocess_exec)
- **Complexity**: Low
- **Dependencies**: None (built-in)
- **Setup**: Immediate
- **Scaling**: Single machine only
- **Monitoring**: Custom logging
- **Real-time streaming**: Easy (direct stdout/stderr)

#### 2. Celery + Redis/RabbitMQ
- **Complexity**: Medium-High
- **Dependencies**: celery, redis/rabbitmq
- **Setup**: Requires broker infrastructure
- **Scaling**: Horizontal (multiple workers)
- **Monitoring**: Flower dashboard
- **Real-time streaming**: Complex (need custom solution)

#### 3. Background Tasks (FastAPI BackgroundTasks)
- **Complexity**: Low
- **Dependencies**: None
- **Setup**: Immediate
- **Scaling**: Tied to API process
- **Monitoring**: None
- **Real-time streaming**: Difficult

### Decision Rationale

**Chose Subprocess because:**

1. **Current Requirements**:
   - Single experiment at a time (enforced queue)
   - Single machine deployment
   - Real-time progress streaming is critical
   - No need for distributed execution yet

2. **Simplicity**:
   - Zero infrastructure overhead
   - No broker to manage
   - Direct stdout/stderr capture
   - Immediate deployment

3. **Performance**:
   - Low overhead
   - Direct process control
   - Efficient for single-machine workloads

4. **Development Speed**:
   - Already implemented and working
   - Easy to debug
   - Simple error handling

### Migration Path to Celery

**When to migrate:**
- Need parallel experiment execution
- Want to scale across multiple machines
- API server restarts should not kill training
- Need advanced monitoring/retry logic

**Migration strategy:**
1. Keep the Strategy pattern (TrainingExecutor interface)
2. Implement CeleryExecutor (or DockerExecutor) alongside DirectExecutor via the `TrainingExecutor` ABC
3. Switch via configuration flag
4. Minimal code changes (just swap executor)

### Current Implementation Improvements

To make subprocess production-ready:
- ✅ Comprehensive logging
- ✅ Error handling with full context
- ✅ WebSocket streaming for real-time updates
- ✅ Single experiment queue
- ✅ Process lifecycle management
- ⏳ Graceful shutdown handling (TODO)
- ⏳ Resource cleanup on failure (TODO)

### Conclusion

Subprocess is the right choice for current scale and requirements. The Strategy pattern allows easy migration to Celery when needed without rewriting the entire system.