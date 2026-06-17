#!/bin/bash
# Quick diagnostic script to identify infinite rerun issue

echo "🔍 UQLab Streamlit Infinite Rerun Diagnostic"
echo "=============================================="
echo ""

# Check if in correct directory
if [ ! -f "streamlit_app_progressive.py" ]; then
    echo "❌ Error: Must run from uqlab-streamlit directory"
    exit 1
fi

echo "📋 Test 1: Minimal Streamlit App"
echo "This should load quickly and show a counter that stays at 1"
echo "Press Ctrl+C after 10 seconds if it works correctly"
echo ""
read -p "Press Enter to start test 1..."
streamlit run test_minimal.py &
MINIMAL_PID=$!
sleep 15
kill $MINIMAL_PID 2>/dev/null
echo ""
echo "✅ Test 1 complete"
echo ""

echo "📋 Test 2: Startup Diagnostic"
echo "This will show execution count - should be 1-2 on startup"
echo "If it keeps increasing, there's an infinite loop"
echo "Press Ctrl+C after 10 seconds"
echo ""
read -p "Press Enter to start test 2..."
streamlit run diagnose_startup.py &
DIAG_PID=$!
sleep 15
kill $DIAG_PID 2>/dev/null
echo ""
echo "✅ Test 2 complete"
echo ""

echo "📋 Test 3: Backend Health Check"
echo "Checking if backend is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running and healthy"
else
    echo "❌ Backend is NOT running or not responding"
    echo "   Run: ./start_backend.sh"
fi
echo ""

echo "📋 Test 4: Check for Running Streamlit Processes"
STREAMLIT_PROCS=$(ps aux | grep streamlit | grep -v grep | wc -l)
if [ $STREAMLIT_PROCS -gt 0 ]; then
    echo "⚠️  Found $STREAMLIT_PROCS running Streamlit process(es)"
    echo "   You may want to kill them: pkill -f streamlit"
else
    echo "✅ No stray Streamlit processes found"
fi
echo ""

echo "=============================================="
echo "🎯 Summary & Next Steps:"
echo ""
echo "1. If Test 1 worked (counter stayed at 1):"
echo "   → Streamlit itself is working fine"
echo ""
echo "2. If Test 2 showed execution count > 5:"
echo "   → There IS an infinite loop - check terminal output"
echo ""
echo "3. If backend check failed:"
echo "   → Start backend first: ./start_backend.sh"
echo ""
echo "4. Now try the main app:"
echo "   streamlit run streamlit_app_progressive.py"
echo ""
echo "   Expected: 10-30 seconds of 'running man' during import"
echo "   Then it should stop and show the UI"
echo ""
echo "5. If 'running man' never stops (60+ seconds):"
echo "   → Share the terminal output with the developer"
echo ""
echo "See INFINITE_RERUN_TROUBLESHOOTING.md for detailed guide"
echo "=============================================="

# Made with Bob
