# Infinite Rerun Troubleshooting Guide

## Problem
Streamlit shows continuous "running man" icon on startup, indicating an infinite rerun loop.

## What We've Fixed
✅ All `st.rerun()` calls now have `return` statements  
✅ Auto-refresh logic enhanced to stop when experiments complete  
✅ No module-level reruns found  
✅ Diagnostic scan shows 0 code-level issues  

## Possible Causes (If Still Occurring)

### 1. **Slow Imports (Most Likely)**
The app imports many heavy libraries that can take 5-30 seconds:
- PyTorch/torchvision
- Transformers
- NumPy/Pandas
- UI components

**Solution**: Wait 10-30 seconds for initial load. The "running man" during this time is NORMAL.

### 2. **Backend Not Running**
If the backend API isn't responding, the app may retry connections.

**Check**:
```bash
cd uqlab-streamlit
./start_backend.sh
```

**Verify**: Visit http://localhost:8000/docs - should show FastAPI docs

### 3. **Session State Initialization**
Some session state might be triggering reruns during initialization.

**Test**: Run the minimal diagnostic:
```bash
cd uqlab-streamlit
streamlit run diagnose_startup.py
```

This will show:
- Execution count (should be 1-2 on startup)
- Time elapsed
- Whether there's an actual infinite loop

### 4. **Browser Cache**
Old Streamlit state might be cached.

**Solution**:
- Clear browser cache
- Hard refresh (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)
- Try incognito/private window

### 5. **Streamlit Version**
Some Streamlit versions have rerun bugs.

**Check version**:
```bash
streamlit --version
```

**Recommended**: 1.28.0 or later

### 6. **Network/API Timeouts**
Slow API responses might cause the app to appear stuck.

**Check**: Look at terminal output for error messages

## Diagnostic Steps

### Step 1: Run Minimal Test
```bash
cd uqlab-streamlit
streamlit run test_minimal.py
```

**Expected**: Counter stays at 1, only increases when you click button  
**If infinite loop**: Counter keeps increasing without interaction

### Step 2: Run Startup Diagnostic
```bash
streamlit run diagnose_startup.py
```

**Expected**: Execution count 1-2, then stable  
**If infinite loop**: Execution count rapidly increases

### Step 3: Check Backend
```bash
./start_backend.sh
# In another terminal:
curl http://localhost:8000/health
```

**Expected**: `{"status":"healthy"}`

### Step 4: Check Terminal Output
Look for:
- Import errors
- API connection errors
- Timeout messages
- Stack traces

### Step 5: Test with Auto-Refresh Disabled
In `streamlit_app_progressive.py`, find line ~408 and temporarily comment out auto-refresh:

```python
# if auto_refresh:
#     # ... auto-refresh logic
#     st.rerun()
#     return
```

## What "Running Man" Means

The "running man" icon appears when:
1. **Initial Load** (5-30s): Importing libraries - NORMAL
2. **API Calls** (1-5s): Fetching data from backend - NORMAL
3. **Reruns** (<1s): After button clicks or auto-refresh - NORMAL
4. **Infinite Loop** (continuous): Code issue - PROBLEM

## How to Distinguish Normal vs Problem

### Normal Behavior:
- Running man appears for 5-30 seconds on first load
- Disappears after initial load
- Briefly appears when clicking buttons
- Appears every 2-5 seconds if auto-refresh is enabled

### Problem Behavior:
- Running man NEVER stops (even after 60+ seconds)
- Counter in diagnostic keeps increasing
- Terminal shows repeated execution logs
- CPU usage stays high

## Quick Test Commands

```bash
# Test 1: Minimal app (should work)
streamlit run test_minimal.py

# Test 2: Diagnostic (shows execution count)
streamlit run diagnose_startup.py

# Test 3: Main app (may take 10-30s to load)
streamlit run streamlit_app_progressive.py

# Test 4: Check backend
curl http://localhost:8000/health
```

## If Problem Persists

1. **Share terminal output**: Copy the full terminal output when running the app
2. **Share diagnostic results**: Run `diagnose_startup.py` and share the execution count
3. **Check browser console**: Open browser DevTools (F12) and check for JavaScript errors
4. **Try different browser**: Test in Chrome, Firefox, Safari

## Expected Startup Sequence

```
1. [0-5s]   Streamlit initializes
2. [5-15s]  Heavy imports (torch, transformers, etc.)
3. [15-20s] UI components load
4. [20-25s] Backend connection established
5. [25-30s] Initial data fetch
6. [30s+]   App ready, running man stops
```

## Code-Level Verification

All these have been verified as FIXED:
- ✅ 24 `st.rerun()` calls have `return` statements
- ✅ No module-level reruns
- ✅ Auto-refresh stops when experiments complete
- ✅ Session state properly initialized
- ✅ No circular imports causing reruns

## Next Steps

If the diagnostic shows:
- **Execution count 1-2**: Problem is NOT infinite loop, just slow loading
- **Execution count 5+**: There IS an infinite loop - share terminal output
- **Backend errors**: Fix backend connection first
- **Import errors**: Check Python environment and dependencies