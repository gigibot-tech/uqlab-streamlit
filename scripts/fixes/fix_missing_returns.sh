#!/bin/bash
# Script to add 'return' statements after 'st.rerun()' calls
# This fixes the infinite rerun loop bug

echo "🔍 Finding Python files with st.rerun()..."

# Find all Python files with st.rerun() and fix them
find . -name "*.py" -type f ! -path "*/.venv/*" ! -path "*/__pycache__/*" | while read -r file; do
    # Check if file contains st.rerun()
    if grep -q "st\.rerun()" "$file"; then
        echo "📝 Processing: $file"
        
        # Use sed to add return after st.rerun() if not already present
        # This regex looks for st.rerun() followed by anything except 'return' on the next line
        sed -i.bak '/st\.rerun()/!b; n; /^[[:space:]]*return/b; i\
        return  # CRITICAL: Stop execution after rerun
' "$file"
        
        # Check if file was modified
        if ! cmp -s "$file" "$file.bak"; then
            echo "✅ Fixed: $file"
            rm "$file.bak"
        else
            echo "⏭️  Skipped (already has return): $file"
            rm "$file.bak"
        fi
    fi
done

echo ""
echo "✨ Done! All st.rerun() calls now have return statements."
echo ""
echo "🧪 Test the app to verify the fix works:"
echo "   cd uqlab-streamlit && streamlit run streamlit_app_progressive.py"

# Made with Bob
