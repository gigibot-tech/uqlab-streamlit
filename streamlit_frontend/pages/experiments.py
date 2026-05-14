"""Experiments Page with Authentication"""
import streamlit as st
import pandas as pd
from services.api_client import APIClient

def login_form():
    """Display login form"""
    st.warning("⚠️ Authentication Required")
    with st.form("login_form"):
        username = st.text_input("Username", value="admin@example.com")
        password = st.text_input("Password", type="password", value="changethis")
        if st.form_submit_button("Login"):
            return username, password
    return None, None

def render(api_client: APIClient):
    st.title("🧪 Experiments")
    
    # Check if logged in
    if "access_token" not in st.session_state:
        username, password = login_form()
        if username and password:
            try:
                # Login
                response = api_client.post("/api/v1/login/access-token", {
                    "username": username,
                    "password": password
                })
                st.session_state.access_token = response["access_token"]
                api_client.token = response["access_token"]
                st.success("✅ Logged in!")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")
        return
    
    # Logged in - show experiments
    tab1, tab2 = st.tabs(["Create", "View"])
    
    with tab1:
        with st.form("exp_form"):
            name = st.text_input("Name", value=f"exp_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}")
            epochs = st.number_input("Epochs", 1, 100, 12)
            lr = st.number_input("Learning Rate", 0.0001, 0.1, 0.001, format="%.4f")
            
            if st.form_submit_button("Create"):
                try:
                    result = api_client.post("/api/v1/experiments/", {
                        "name": name,
                        "config": {
                            "noise_type": "worse_label",
                            "under_supported_classes": "3,5",
                            "under_train_per_class": 50,
                            "regular_train_per_class": 300,
                            "eval_per_group": 600,
                            "dinov2_model": "small",
                            "hidden_dim": 256,
                            "dropout": 0.2,
                            "epochs": epochs,
                            "learning_rate": lr,
                            "weight_decay": 0.0001,
                            "train_batch_size": 256,
                            "mc_passes": 20,
                            "attribution_method": "dualxda"
                        }
                    })
                    st.success(f"Created: {result['name']}")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with tab2:
        try:
            exps = api_client.get("/api/v1/experiments/")
            if exps:
                data = [{
                    "Name": e["name"],
                    "Status": e["status"],
                    "Created": pd.to_datetime(e["created_at"]).strftime("%Y-%m-%d %H:%M")
                } for e in exps]
                st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
            else:
                st.info("No experiments yet")
        except Exception as e:
            st.error(f"Error: {e}")
