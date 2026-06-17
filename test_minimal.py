"""
Minimal Streamlit app to test if basic functionality works without infinite reruns.
"""
import streamlit as st

st.title("Minimal Test App")

# Initialize session state
if 'counter' not in st.session_state:
    st.session_state.counter = 0
    st.write("✅ Session state initialized")

st.write(f"Page has loaded {st.session_state.counter} times")
st.session_state.counter += 1

# Test button
if st.button("Test Button"):
    st.success("Button clicked!")
    st.rerun()

st.write("If you see this and the counter keeps increasing without clicking anything, there's an infinite loop.")
st.write("If the counter stays at 1 and only increases when you click the button, everything is working correctly.")

# Made with Bob
