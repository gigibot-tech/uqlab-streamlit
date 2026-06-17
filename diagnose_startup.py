"""
Comprehensive diagnostic script to identify what's causing continuous reruns.
Run this to see exactly what's happening during startup.
"""
import streamlit as st
import time
from datetime import datetime

st.title("🔍 Startup Diagnostic Tool")

# Track execution
if 'execution_log' not in st.session_state:
    st.session_state.execution_log = []
    st.session_state.rerun_count = 0
    st.session_state.start_time = time.time()

# Log this execution
current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
st.session_state.rerun_count += 1
elapsed = time.time() - st.session_state.start_time

log_entry = f"[{current_time}] Execution #{st.session_state.rerun_count} (elapsed: {elapsed:.2f}s)"
st.session_state.execution_log.append(log_entry)

# Display status
st.metric("Total Executions", st.session_state.rerun_count)
st.metric("Time Elapsed", f"{elapsed:.2f}s")

# Warning if too many reruns
if st.session_state.rerun_count > 5:
    st.error(f"⚠️ INFINITE LOOP DETECTED! Script has run {st.session_state.rerun_count} times in {elapsed:.2f}s")
    st.error("This indicates an infinite rerun loop somewhere in your code.")
elif st.session_state.rerun_count > 2:
    st.warning(f"⚠️ Multiple reruns detected ({st.session_state.rerun_count} times)")
else:
    st.success("✅ Normal execution pattern")

# Show execution log
with st.expander("📋 Execution Log", expanded=True):
    for entry in st.session_state.execution_log[-20:]:  # Show last 20
        st.text(entry)

# Test auto-refresh pattern
st.markdown("---")
st.subheader("🔄 Auto-Refresh Test")

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

col1, col2 = st.columns(2)
with col1:
    if st.button("Enable Auto-Refresh"):
        st.session_state.auto_refresh = True
        st.rerun()
        
with col2:
    if st.button("Disable Auto-Refresh"):
        st.session_state.auto_refresh = False
        st.rerun()

st.write(f"Auto-refresh status: **{'ENABLED' if st.session_state.auto_refresh else 'DISABLED'}**")

# This is the pattern that should work correctly
if st.session_state.auto_refresh:
    st.info("🔄 Auto-refresh is enabled. Refreshing every 2 seconds...")
    time.sleep(2)
    st.rerun()

st.markdown("---")
st.markdown("""
### 📊 What to Look For:

1. **Normal Behavior**: 
   - Execution count should be 1-2 on initial load
   - Should only increase when you click buttons
   
2. **Infinite Loop**:
   - Execution count rapidly increases without user interaction
   - Time elapsed increases but count keeps going up
   
3. **Auto-Refresh**:
   - When enabled, should refresh every 2 seconds (controlled)
   - When disabled, should stop refreshing
""")

# Made with Bob
