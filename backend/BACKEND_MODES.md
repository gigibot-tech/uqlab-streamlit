# Backend Server Modes

The UQLab backend can run in two different modes: **Development Mode** and **Production Mode**. Understanding when to use each mode is critical for preventing experiment failures.

---

## 🚨 Critical Issue: Auto-Reload Kills Running Experiments

When the backend runs with auto-reload enabled (development mode), **any code change will immediately restart the server**. This causes:

1. **Experiment Termination**: Running experiments are killed mid-execution
2. **Data Loss**: No results are saved from interrupted experiments
3. **Pickle Errors**: Multiprocessing operations fail with truncated pickle data
4. **Wasted Time**: Hours of computation can be lost instantly

---

## Development Mode (with Auto-Reload)

### When to Use
- ✅ Rapid prototyping and testing
- ✅ Making frequent code changes
- ✅ Testing API endpoints
- ✅ UI development work
- ✅ Short-running operations

### When NOT to Use
- ❌ **Running experiments** (they will be killed!)
- ❌ Long-running background tasks
- ❌ Production deployments
- ❌ Batch processing jobs

### How to Start
```bash
cd backend
./start_backend.sh
```

### What Happens
- Server watches `backend/app/`, `src/`, and `scripts/` directories
- Any file change triggers an immediate server restart
- All running processes are terminated
- Server restarts with updated code

### Technical Details
- Uses `uvicorn` with `--reload` flag
- Monitors multiple directories with WatchFiles
- Hot-reloads Python modules automatically
- Runs via `run_dev.py`

---

## Production Mode (NO Auto-Reload)

### When to Use
- ✅ **Running experiments** (ALWAYS use this!)
- ✅ Long-running background tasks
- ✅ Production deployments
- ✅ Batch processing
- ✅ Any operation that takes >1 minute

### When NOT to Use
- ❌ Active development with frequent code changes
- ❌ When you need immediate feedback on code changes

### How to Start
```bash
cd backend
./start_backend_prod.sh
```

### What Happens
- Server starts without file watching
- Code changes do NOT trigger restarts
- Running experiments complete without interruption
- Must manually restart to apply code changes

### Technical Details
- Uses `uvicorn` WITHOUT `--reload` flag
- No file watching or monitoring
- Stable process that runs until manually stopped
- Runs via `run_prod.py`

---

## Quick Reference

| Feature | Development Mode | Production Mode |
|---------|-----------------|-----------------|
| **Auto-reload** | ✅ Yes | ❌ No |
| **File watching** | ✅ Yes | ❌ No |
| **Kills experiments** | ⚠️ YES | ✅ No |
| **Code changes apply** | Immediately | After manual restart |
| **Use for experiments** | ❌ NEVER | ✅ ALWAYS |
| **Startup script** | `start_backend.sh` | `start_backend_prod.sh` |
| **Python script** | `run_dev.py` | `run_prod.py` |

---

## Switching Between Modes

### From Development to Production
1. Stop the development server (Ctrl+C)
2. Start production mode: `./start_backend_prod.sh`
3. Your experiments will now be safe from restarts

### From Production to Development
1. Stop the production server (Ctrl+C)
2. Start development mode: `./start_backend.sh`
3. Code changes will now trigger automatic restarts

---

## Best Practices

### For Developers
1. **Use development mode** for normal coding work
2. **Switch to production mode** before starting any experiment
3. **Never edit code** while experiments are running in production mode
4. **Test changes** in development mode before running experiments

### For Experiment Runners
1. **Always use production mode** (`start_backend_prod.sh`)
2. **Verify the mode** by checking the startup message
3. **Don't edit code** while experiments are running
4. **Wait for completion** before switching back to development mode

### For Production Deployments
1. **Always use production mode**
2. **Never use development mode** in production environments
3. **Use process managers** (systemd, supervisor) for automatic restarts
4. **Monitor logs** for unexpected terminations

---

## Troubleshooting

### Problem: Experiment was killed mid-execution
**Cause**: Backend was running in development mode and code changed  
**Solution**: Always use `start_backend_prod.sh` for experiments

### Problem: Pickle data truncation error
**Cause**: Server restart interrupted multiprocessing operation  
**Solution**: Use production mode to prevent restarts

### Problem: Code changes not taking effect
**Cause**: Running in production mode (expected behavior)  
**Solution**: Stop server (Ctrl+C) and restart to apply changes

### Problem: Need to fix bug during experiment
**Options**:
1. **Wait**: Let experiment complete, then fix and restart
2. **Accept loss**: Stop experiment, fix code, restart in prod mode
3. **Hot patch**: Carefully edit non-critical code (risky!)

---

## Technical Implementation

### Development Mode (`run_dev.py`)
```python
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8000,
    reload=True,  # Auto-reload enabled
    reload_dirs=[backend_dir, src_dir, scripts_dir],
)
```

### Production Mode (`run_prod.py`)
```python
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8000,
    reload=False,  # Auto-reload disabled
)
```

---

## Summary

**Golden Rule**: If you're running an experiment, use production mode (`start_backend_prod.sh`). Period.

The few seconds saved by auto-reload are not worth losing hours of experiment results.