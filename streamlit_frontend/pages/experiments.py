"""Experiments Page - No Auth Version"""
import streamlit as st
import pandas as pd

def render(api_client):
    st.title("🧪 Experiments")
    
    tab1, tab2 = st.tabs(["Create", "View"])
    
    with tab1:
        st.subheader("Create New Experiment")
        with st.form("exp_form"):
            name = st.text_input("Name", value=f"exp_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}")
            
            col1, col2 = st.columns(2)
            with col1:
                epochs = st.number_input("Epochs", 1, 100, 12)
                lr = st.number_input("Learning Rate", 0.0001, 0.1, 0.001, format="%.4f")
            with col2:
                batch_size = st.number_input("Batch Size", 16, 512, 256, step=16)
                mc_passes = st.number_input("MC Passes", 5, 100, 20)
            
            if st.form_submit_button("🚀 Create Experiment", type="primary"):
                try:
                    result = api_client.post("/api/v1/experiments/no-auth", {
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
                            "train_batch_size": batch_size,
                            "mc_passes": mc_passes,
                            "attribution_method": "dualxda"
                        }
                    })
                    st.success(f"✅ Created: {result['name']}")
                    st.json(result)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with tab2:
        st.subheader("All Experiments")
        if st.button("🔄 Refresh"):
            st.rerun()
        
        try:
            exps = api_client.get("/api/v1/experiments/no-auth")
            if exps:
                data = []
                for e in exps:
                    data.append({
                        "Name": e["name"],
                        "Status": e["status"],
                        "Progress": f"{e.get('progress', 0):.1%}",
                        "Created": pd.to_datetime(e["created_at"]).strftime("%Y-%m-%d %H:%M"),
                        "Aleatoric": f"{e['aleatoric_auroc']:.3f}" if e.get('aleatoric_auroc') else "N/A",
                        "Epistemic": f"{e['epistemic_auroc']:.3f}" if e.get('epistemic_auroc') else "N/A"
                    })
                st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
            else:
                st.info("No experiments yet. Create one in the 'Create' tab!")
        except Exception as e:
            st.error(f"❌ Error loading experiments: {e}")
